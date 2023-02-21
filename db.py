import psycopg2
import json

from psycopg2.extensions import cursor, connection

dbname = "schedulerdb"
user = "postgres"
password = ""
host = "localhost"
port = "5432"


def connect_to_db() -> tuple[cursor, connection]:
    try:
        conn = psycopg2.connect(dbname=dbname, user=user,
                                password=password, host=host, port=port)
        print("Successfully connected to database!")
    except psycopg2.OperationalError as e:
        # If the database doesn't exist, create it
        if "database" in str(e) and "does not exist" in str(e):
            conn = psycopg2.connect(
                user=user, password=password, host=host, port=port)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE {dbname}")
            cur.close()
            conn.close()
            # Connect to the newly created database
            conn = psycopg2.connect(dbname=dbname, user=user,
                                    password=password, host=host, port=port)
            print("Successfully created and connected to database!")
        else:
            raise e

    # Create a cursor object
    cur = conn.cursor()

    return cur, conn


def populate_db(data: dict):
    cur, conn = connect_to_db()

    if not do_tables_exist(cur):
        create_tables(cur, conn)

    for course in data.values():
        course_id = insert_course(cur, course)
        instructor_ids = insert_instructors(cur, course)

        for instructor_id in instructor_ids:
            insert_course_instructor(cur, course_id, instructor_id)

    conn.commit()

    cur.close()
    conn.close()


def insert_course_instructor(cur: cursor, course_id: int, instructor_id: int):
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
            INSERT INTO instructors (name)
            VALUES (%s)
            RETURNING id
            """, (instructor["name"],))

    instructor_id = cur.fetchone()[0]

    if instructor["rating"] is not None:
        cur.execute("""
            UPDATE instructors
            SET avg_difficulty = %s, avg_rating = %s, num_ratings = %s
            WHERE id = %s
            """, (instructor["rating"]["avgDifficulty"], instructor["rating"]["avgRating"], instructor["rating"]["numRatings"], instructor_id))

    return instructor_id


def insert_course(cur: cursor, course) -> int:
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
    print("Tables created successfully!")


def do_tables_exist(cur: cursor):
    cur.execute("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_name IN ('courses', 'instructors')
""")
    return cur.fetchone()[0] == 2


with open("data.json") as f:
    data = json.load(f)

populate_db(data)
