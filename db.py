import psycopg2
from db_config import DBNAME, USER, PASSWORD, HOST, PORT, DEFAULT_DB

from psycopg2.extensions import cursor, connection


def populate_db(data: dict):
    cur, conn = connect_to_db()

    if not do_tables_exist(cur):
        create_tables(cur, conn)

    for course in data.values():
        course_id = insert_course(cur, course)
        instructor_ids = insert_instructors(cur, course)

        for instructor_id in instructor_ids:
            insert_course_instructor(cur, course_id, instructor_id)

    delete_old_data(cur, data)

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

    if not course_instructor_in_db(cur, course_id, instructor_id):
        insert_new_course_instructor(cur, course_id, instructor_id)


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
    if not instructor_name_in_db(cur, instructor["name"]):
        insert_new_instructor(cur, instructor)
    return update_instructor(cur, instructor)


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
            SET avg_difficulty = %s, avg_rating = %s, num_ratings = %s
            WHERE name = %s
            RETURNING id
            """, (instructor["rating"]["avgDifficulty"], instructor["rating"]["avgRating"], instructor["rating"]["numRatings"], instructor["name"]))

    return cur.fetchone()[0]


def insert_new_instructor(cur: cursor, instructor) -> int:
    cur.execute("""
        INSERT INTO instructors (name)
        VALUES (%s)
        RETURNING id
        """, (instructor["name"],))

    return cur.fetchone()[0]


def insert_course(cur: cursor, course) -> int:
    if crn_in_db(cur, course["crn"]):
        return update_course(cur, course)
    else:
        return insert_new_course(cur, course)


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
        SET subject_code = %s, course_number = %s, instruction_type = %s, instruction_method = %s, section = %s, enroll = %s, max_enroll = %s, course_title = %s, start_time = %s, end_time = %s, days = %s
        WHERE crn = %s
        RETURNING crn
        """, (course["subject_code"], course["course_number"], course["instruction_type"], course["instruction_method"],
              course["section"], course["enroll"], course["max_enroll"], course["course_title"], course["start_time"], course["end_time"], course["days"], course["crn"]))

    return cur.fetchone()[0]


def insert_new_course(cur: cursor, course) -> int:
    cur.execute("""
        INSERT INTO courses (crn, subject_code, course_number, instruction_type, instruction_method, section, enroll, max_enroll, course_title, start_time, end_time, days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING crn
        """, (course["crn"], course["subject_code"], course["course_number"], course["instruction_type"], course["instruction_method"],
              course["section"], course["enroll"], course["max_enroll"], course["course_title"], course["start_time"], course["end_time"], course["days"]))

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
    WHERE table_name IN('courses', 'instructors')
""")
    return cur.fetchone()[0] == 2
