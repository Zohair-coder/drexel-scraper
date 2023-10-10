import psycopg2
from psycopg2 import sql
from psycopg2.extensions import cursor, connection

from db_config import DBNAME, USER, PASSWORD, HOST, PORT, DEFAULT_DB, GRAFANA_SERVICE_ACCOUNT_USERNAME, GRAFANA_SERVICE_ACCOUNT_PASSWORD

from datetime import datetime
from pytz import timezone

def populate_db(data: dict):
    cur, conn = connect_to_db()

    if not do_tables_exist(cur):
        create_tables(cur, conn)
    
    if not grafana_user_exists(cur):
        create_grafana_user(cur)
    
    assign_grafana_user_permissions(cur)

    update_metadata(cur)

    delete_old_data(cur, data)
    
    for course in data.values():
        course_id = insert_course(cur, course)
        instructor_ids = insert_instructors(cur, course)

        for instructor_id in instructor_ids:
            insert_course_instructor(cur, course_id, instructor_id)

    conn.commit()

    cur.close()
    conn.close()

def connect_to_db() -> tuple[cursor, connection]:
    try:
        conn = psycopg2.connect(dbname=DBNAME.lower(), user=USER,
                                password=PASSWORD, host=HOST, port=PORT)
    except psycopg2.OperationalError as e:
        # If the database doesn't exist, create it
        if "database" in str(e) and "does not exist" in str(e):
            conn = psycopg2.connect(
                dbname=DEFAULT_DB.lower(), user=USER, password=PASSWORD, host=HOST, port=PORT)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE {DBNAME}")
            cur.close()
            conn.close()
            # Connect to the newly created database
            conn = psycopg2.connect(dbname=DBNAME.lower(), user=USER,
                                    password=PASSWORD, host=HOST, port=PORT)
        else:
            raise e

    # Create a cursor object
    cur = conn.cursor()

    return cur, conn

def delete_old_data(cur: cursor, data: dict):
    crns = [course["crn"] for course in data.values()]

    cur.execute("""
        DELETE FROM course_instructor
        WHERE course_id NOT IN %s
        """, (tuple(crns),))

    cur.execute("""
        DELETE FROM courses
        WHERE crn NOT IN (
            SELECT course_id
            FROM course_instructor
        )
        """)

    cur.execute("""
        DELETE FROM instructors
        WHERE id NOT IN (
            SELECT instructor_id
            FROM course_instructor
        )
        """)

def insert_course_instructor(cur: cursor, course_id: int, instructor_id: int):
    cur.execute("""
        INSERT INTO course_instructor (course_id, instructor_id)
        VALUES (%s, %s)
        ON CONFLICT (course_id, instructor_id)
        DO NOTHING
    """, (course_id, instructor_id))


def course_instructor_in_db(cur: cursor, course_id: int, instructor_id: int) -> bool:
    cur.execute("""
        SELECT COUNT(*)
        FROM course_instructor
        WHERE course_id = %s AND instructor_id = %s
        """, (course_id, instructor_id))

    return cur.fetchone()[0] == 1


def insert_new_course_instructor(cur: cursor, course_id: int, instructor_id: int):
    cur.execute("""
        INSERT INTO course_instructor (course_id, instructor_id)
        VALUES (%s, %s)
        """, (course_id, instructor_id))


def insert_instructors(cur, course):
    if course["instructors"] is None:
        return []

    instructor_ids = []

    for instructor in course["instructors"]:
        instructor_id = insert_instructor(cur, instructor)
        instructor_ids.append(instructor_id)

    return instructor_ids


def insert_instructor(cur: cursor, instructor) -> int:
    cur.execute("""
        INSERT INTO instructors (name, rmp_id, avg_difficulty, avg_rating, num_ratings)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name)
        DO UPDATE SET 
            rmp_id = EXCLUDED.rmp_id,
            avg_difficulty = EXCLUDED.avg_difficulty,
            avg_rating = EXCLUDED.avg_rating,
            num_ratings = EXCLUDED.num_ratings
        RETURNING id
    """, (instructor["name"],
          instructor["rating"]["legacyId"] if instructor.get("rating", None) is not None else None,
          instructor["rating"]["avgDifficulty"] if instructor.get("rating", None) is not None else None,
          instructor["rating"]["avgRating"] if instructor.get("rating", None) is not None else None,
          instructor["rating"]["numRatings"] if instructor.get("rating", None) is not None else None
    ))

    return cur.fetchone()[0]


def instructor_name_in_db(cur: cursor, name: str) -> bool:
    cur.execute("""
        SELECT COUNT(*)
        FROM instructors
        WHERE name = %s
        """, (name,))

    return cur.fetchone()[0] == 1


def update_instructor(cur: cursor, instructor) -> int:
    if instructor.get("rating", None) is None:
        cur.execute("""
            SELECT id
            FROM instructors
            WHERE name = %s
            """, (instructor["name"],))
    else:
        cur.execute("""
            UPDATE instructors
            SET rmp_id = %s, avg_difficulty = %s, avg_rating = %s, num_ratings = %s
            WHERE name = %s
            RETURNING id
            """, (instructor["rating"]["legacyId"], instructor["rating"]["avgDifficulty"], instructor["rating"]["avgRating"], instructor["rating"]["numRatings"], instructor["name"]))

    return cur.fetchone()[0]


def insert_new_instructor(cur: cursor, instructor) -> int:
    cur.execute("""
        INSERT INTO instructors (name)
        VALUES (%s)
        RETURNING id
        """, (instructor["name"],))

    return cur.fetchone()[0]


def insert_course(cur: cursor, course) -> int:
    cur.execute("""
        INSERT INTO courses (crn, subject_code, course_number, instruction_type, instruction_method, section, enroll, max_enroll, course_title, credits, start_time, end_time, days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (crn)
        DO UPDATE SET 
            subject_code = EXCLUDED.subject_code, 
            course_number = EXCLUDED.course_number, 
            instruction_type = EXCLUDED.instruction_type, 
            instruction_method = EXCLUDED.instruction_method,
            section = EXCLUDED.section,
            enroll = EXCLUDED.enroll,
            max_enroll = EXCLUDED.max_enroll,
            course_title = EXCLUDED.course_title,
            credits = EXCLUDED.credits,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            days = EXCLUDED.days
        RETURNING crn
    """, (course["crn"], course["subject_code"], course["course_number"], course["instruction_type"], course["instruction_method"],
          course["section"], course["enroll"], course["max_enroll"], course["course_title"], course["credits"], course["start_time"], course["end_time"], course["days"]))
    
    return cur.fetchone()[0]



def crn_in_db(cur: cursor, crn: int) -> bool:
    cur.execute("""
        SELECT COUNT(*)
        FROM courses
        WHERE crn = %s
        """, (crn,))

    return cur.fetchone()[0] == 1


def update_course(cur: cursor, course) -> int:
    cur.execute("""
        UPDATE courses
        SET subject_code = %s, course_number = %s, instruction_type = %s, instruction_method = %s, section = %s, enroll = %s, max_enroll = %s, course_title = %s, credits = %s, start_time = %s, end_time = %s, days = %s
        WHERE crn = %s
        RETURNING crn
        """, (course["subject_code"], course["course_number"], course["instruction_type"], course["instruction_method"],
              course["section"], course["enroll"], course["max_enroll"], course["course_title"], course["credits"], course["start_time"], course["end_time"], course["days"], course["crn"]))

    return cur.fetchone()[0]


def insert_new_course(cur: cursor, course) -> int:
    cur.execute("""
        INSERT INTO courses (crn, subject_code, course_number, instruction_type, instruction_method, section, enroll, max_enroll, course_title, credits, start_time, end_time, days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING crn
        """, (course["crn"], course["subject_code"], course["course_number"], course["instruction_type"], course["instruction_method"],
              course["section"], course["enroll"], course["max_enroll"], course["course_title"], course["credits"], course["start_time"], course["end_time"], course["days"]))

    return cur.fetchone()[0]


def create_tables(cur: cursor, conn: connection):
    with open("create_tables.sql") as f:
        create_table_sql = f.read()

    cur.execute(create_table_sql)
    conn.commit()


def do_tables_exist(cur: cursor):
    cur.execute("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_name IN('courses', 'instructors', 'course_instructor', 'metadata')
""")
    return cur.fetchone()[0] == 4

def update_metadata(cur: cursor):
    tz = timezone('US/Eastern')
    current_datetime = datetime.now(tz).strftime("%m/%d/%y %I:%M %p")
    cur.execute("""
    INSERT INTO metadata (key, value)
      VALUES ('last_updated', %s)
      ON CONFLICT (key)
      DO UPDATE SET value = EXCLUDED.value;
""", (current_datetime,))
    
def grafana_user_exists(cur: cursor):
    grafana_user = GRAFANA_SERVICE_ACCOUNT_USERNAME
    cur.execute("""
    SELECT 1
    FROM pg_roles
    WHERE rolname = %s
""", (grafana_user,))
    row = cur.fetchone()
    return row is not None and row[0] == 1

def create_grafana_user(cur: cursor):
    grafana_username = GRAFANA_SERVICE_ACCOUNT_USERNAME
    grafana_password = GRAFANA_SERVICE_ACCOUNT_PASSWORD

    create_role_command = sql.SQL(
            "CREATE ROLE {} WITH LOGIN PASSWORD %s;"
        ).format(sql.Identifier(grafana_username))
    
    cur.execute(create_role_command, [grafana_password])

def assign_grafana_user_permissions(cur: cursor):
    grafana_username = GRAFANA_SERVICE_ACCOUNT_USERNAME
    cmd = sql.SQL(
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO {};"
    ).format(sql.Identifier(grafana_username))
    cur.execute(cmd)