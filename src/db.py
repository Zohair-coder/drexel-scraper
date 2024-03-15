import psycopg2
from psycopg2 import sql
from psycopg2.extensions import cursor, connection

from db_config import DBNAME, USER, PASSWORD, HOST, PORT, DEFAULT_DB, GRAFANA_SERVICE_ACCOUNT_USERNAME, GRAFANA_SERVICE_ACCOUNT_PASSWORD

from datetime import datetime
from pytz import timezone
import sys

def populate_db(data: dict):
    cur, conn = connect_to_db()
    
    create_tables(cur)
    
    if not grafana_user_exists(cur):
        create_grafana_user(cur)
    
    assign_grafana_user_permissions(cur)
    update_metadata(cur)

    course_instructor_relationships = []
    for course in data.values():
        instructor_ids = bulk_insert_instructors(cur, course)

        for instructor_id in instructor_ids:
            course_instructor_relationships.append((course["crn"], instructor_id))

    bulk_insert_courses(cur, data.values())
    bulk_insert_course_instructors(cur, course_instructor_relationships)

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

def bulk_insert_course_instructors(cur: cursor, relationships: list[tuple[int, int]]):
    cur.executemany("""
        INSERT INTO course_instructor (course_id, instructor_id)
        VALUES (%s, %s)
        ON CONFLICT (course_id, instructor_id)
        DO NOTHING
    """, relationships)


def bulk_insert_instructors(cur: cursor, course: dict) -> list[int]:
    if course["instructors"] is None:
        return []

    instructor_data = []
    instructor_names = []
    for instructor in course["instructors"]:
        instructor_data.append((
            instructor["name"],
            instructor["rating"]["legacyId"] if instructor.get("rating", None) is not None else None,
            instructor["rating"]["avgDifficulty"] if instructor.get("rating", None) is not None else None,
            instructor["rating"]["avgRating"] if instructor.get("rating", None) is not None else None,
            instructor["rating"]["numRatings"] if instructor.get("rating", None) is not None else None
        ))

        instructor_names.append(instructor["name"])

    cur.executemany("""
        INSERT INTO instructors (name, rmp_id, avg_difficulty, avg_rating, num_ratings)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name)
        DO UPDATE SET 
            rmp_id = EXCLUDED.rmp_id,
            avg_difficulty = EXCLUDED.avg_difficulty,
            avg_rating = EXCLUDED.avg_rating,
            num_ratings = EXCLUDED.num_ratings
        RETURNING id
    """, instructor_data)

    cur.execute("""
        SELECT id FROM instructors WHERE name IN %s
    """, (tuple(instructor_names),))

    return [row[0] for row in cur.fetchall()]

def bulk_insert_courses(cur: cursor, courses_data: list[dict]):
    courses = []
    for course in courses_data:
        courses.append((course["crn"], course["subject_code"], course["course_number"], course["instruction_type"], 
                        course["instruction_method"], course["section"], course["enroll"], course["max_enroll"], 
                        course["course_title"], course["credits"], course["prereqs"], course["start_time"], course["end_time"], 
                        course["days"]))

    cur.executemany("""
        INSERT INTO courses (crn, subject_code, course_number, instruction_type, instruction_method, 
                             section, enroll, max_enroll, course_title, credits, prereqs, start_time, end_time, days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            prereqs = EXCLUDED.prereqs,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            days = EXCLUDED.days
    """, courses)

def create_tables(cur: cursor):
    with open("src/create_tables.sql") as f:
        create_table_sql = f.read()

    cur.execute(create_table_sql)

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