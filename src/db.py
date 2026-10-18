"""Transactional term refreshes and a non-destructive legacy migration."""

from contextlib import closing
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import cursor, connection

from db_config import (
    DBNAME,
    USER,
    PASSWORD,
    HOST,
    PORT,
    DEFAULT_DB,
    GRAFANA_SERVICE_ACCOUNT_USERNAME,
    GRAFANA_SERVICE_ACCOUNT_PASSWORD,
)
from terms import term_label, term_url
from quarter_utils import get_current_quarter_and_year


def connect_to_db() -> tuple[cursor, connection]:
    try:
        conn = psycopg2.connect(
            dbname=DBNAME.lower(), user=USER, password=PASSWORD, host=HOST, port=PORT
        )
    except psycopg2.OperationalError as exc:
        if "database" not in str(exc) or "does not exist" not in str(exc):
            raise
        with closing(
            psycopg2.connect(
                dbname=DEFAULT_DB, user=USER, password=PASSWORD, host=HOST, port=PORT
            )
        ) as admin:
            admin.autocommit = True
            with admin.cursor() as cur:
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME.lower()))
                )
        conn = psycopg2.connect(
            dbname=DBNAME.lower(), user=USER, password=PASSWORD, host=HOST, port=PORT
        )
    return conn.cursor(), conn


def initialize(default_term: str | None = None) -> None:
    cur, conn = connect_to_db()
    with closing(conn), conn, cur:
        create_tables(cur)
        set_dashboard_default(cur, default_term)
        cur.execute(
            "SELECT 1 FROM pg_roles WHERE rolname=%s",
            (GRAFANA_SERVICE_ACCOUNT_USERNAME,),
        )
        if cur.fetchone() is None:
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(
                    sql.Identifier(GRAFANA_SERVICE_ACCOUNT_USERNAME)
                ),
                (GRAFANA_SERVICE_ACCOUNT_PASSWORD,),
            )
        cur.execute(
            sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                sql.Identifier(GRAFANA_SERVICE_ACCOUNT_USERNAME)
            )
        )


def create_tables(cur: cursor) -> None:
    # Serializes migrations against refreshes without locking readers.
    cur.execute("SELECT pg_advisory_xact_lock(712410)")
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='courses' AND column_name='crn'), EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='courses' AND column_name='term_code')"
    )
    old, new = cur.fetchone() or (False, False)
    if old and not new:
        # Keep the entire previous schema available for rollback/review.
        cur.execute("CREATE SCHEMA legacy_single_quarter")
        for name in ("metadata", "instructors", "courses", "course_instructor"):
            cur.execute(
                sql.SQL(
                    "ALTER TABLE public.{} SET SCHEMA legacy_single_quarter"
                ).format(sql.Identifier(name))
            )
        cur.execute(
            "ALTER VIEW public.all_course_instructor_data SET SCHEMA legacy_single_quarter"
        )
    cur.execute(Path(__file__).with_name("create_tables.sql").read_text())
    # Upgrade labels from the original multi-quarter release without needing
    # authentication during migration. Preserve labels already supplied by TMS.
    cur.execute(
        "SELECT code FROM terms WHERE label ~ '^(Fall|Winter|Spring|Summer) [0-9]{4}$'"
    )
    for (code,) in cur.fetchall():
        cur.execute("UPDATE terms SET label=%s WHERE code=%s", (term_label(code), code))
    if old and not new:
        cur.execute("SELECT key,value FROM legacy_single_quarter.metadata")
        metadata = dict(cur.fetchall())
        code = metadata["current_year"] + metadata["current_quarter"]
        upsert_term(cur, code)
        cur.execute("""INSERT INTO instructors(id,name,rmp_id,avg_rating,avg_difficulty,num_ratings)
            SELECT id,name,rmp_id,avg_rating,avg_difficulty,num_ratings FROM legacy_single_quarter.instructors""")
        cur.execute(
            "SELECT setval(pg_get_serial_sequence('instructors','id'), COALESCE((SELECT max(id) FROM instructors),1), EXISTS(SELECT 1 FROM instructors))"
        )
        cur.execute(
            """INSERT INTO courses(term_code,crn,subject_code,course_number,course_title,section,instruction_type,instruction_method,enrolled,capacity,is_full,credits,prerequisites,start_time,end_time,days)
            SELECT %s,crn,subject_code,course_number,course_title,section,instruction_type,instruction_method,
                CASE WHEN enroll ~ '^[0-9]+$' THEN enroll::integer END,
                CASE WHEN max_enroll ~ '^[0-9]+$' THEN max_enroll::integer END,
                CASE WHEN enroll='FULL' THEN true WHEN enroll ~ '^[0-9]+$' THEN false END,
                credits,prereqs,start_time,end_time,days FROM legacy_single_quarter.courses""",
            (code,),
        )
        cur.execute(
            "INSERT INTO course_instructors SELECT %s,course_id,instructor_id FROM legacy_single_quarter.course_instructor",
            (code,),
        )
        # Unknown legacy timestamp is deliberately left NULL until a verified refresh.


def upsert_term(cur: cursor, code: str, label: str | None = None) -> None:
    cur.execute(
        """INSERT INTO terms(code,label,source_url) VALUES (%s,%s,%s)
        ON CONFLICT(code) DO UPDATE SET
            label=CASE WHEN %s IS NOT NULL THEN excluded.label ELSE terms.label END,
            source_url=excluded.source_url""",
        (code, label if label is not None else term_label(code), term_url(code), label),
    )


def set_dashboard_default(cur: cursor, default_term: str | None = None) -> None:
    if default_term is None:
        year, quarter = get_current_quarter_and_year()
        default_term = year + quarter
    term_label(default_term)
    cur.execute("UPDATE terms SET is_default=false WHERE is_default")
    cur.execute(
        "UPDATE terms SET is_default=true WHERE code=%s AND available", (default_term,)
    )


def update_catalogue(terms: dict[str, str], default_term: str | None = None) -> None:
    if not terms:
        raise ValueError("Refusing empty catalogue")
    cur, conn = connect_to_db()
    with closing(conn), conn, cur:
        cur.execute("SELECT pg_advisory_xact_lock(712410)")
        cur.execute("UPDATE terms SET available=false")
        for code, label in terms.items():
            upsert_term(cur, code, label)
            cur.execute("UPDATE terms SET available=true WHERE code=%s", (code,))
        set_dashboard_default(cur, default_term)


def number(value: Any) -> int | None:
    return int(value) if value is not None and str(value).isdigit() else None


def populate_db(data: dict[str, dict[str, Any]], term_code: str) -> None:
    """Publish a fully collected term atomically; never truncate other quarters."""
    term_label(term_code)
    if not data:
        raise ValueError("Empty scrape: retaining existing quarter")
    cur, conn = connect_to_db()
    with closing(conn), conn, cur:
        cur.execute("SELECT pg_advisory_xact_lock(712410)")
        upsert_term(cur, term_code)
        cur.execute("DELETE FROM courses WHERE term_code=%s", (term_code,))
        for key, course in data.items():
            if str(course["crn"]) != str(key):
                raise ValueError("CRN key mismatch")
            cur.execute(
                """INSERT INTO courses(term_code,crn,college_code,subject_code,course_number,course_title,section,instruction_type,instruction_method,enrolled,capacity,is_full,credits,prerequisites,start_time,end_time,days)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    term_code,
                    course["crn"],
                    course.get("college_code"),
                    course["subject_code"],
                    course["course_number"],
                    course["course_title"],
                    course["section"],
                    course["instruction_type"],
                    course["instruction_method"],
                    number(course["enroll"]),
                    number(course["max_enroll"]),
                    course["enroll"] == "FULL"
                    if course["enroll"] is not None
                    else None,
                    course.get("credits"),
                    course.get("prereqs"),
                    course.get("start_time"),
                    course.get("end_time"),
                    course.get("days"),
                ),
            )
            for instructor in course["instructors"] or []:
                rating = instructor.get("rating") or {}
                rmp_id = rating.get("legacyId")
                # Reuse only a unique name + RMP match. Never merge by name alone.
                cur.execute(
                    "SELECT id FROM instructors WHERE name=%s AND rmp_id=%s",
                    (instructor["name"], rmp_id),
                )
                matches = cur.fetchall()
                if len(matches) == 1:
                    instructor_id = matches[0][0]
                    cur.execute(
                        "UPDATE instructors SET avg_rating=%s,avg_difficulty=%s,num_ratings=%s,ratings_updated_at=now() WHERE id=%s",
                        (
                            rating.get("avgRating"),
                            rating.get("avgDifficulty"),
                            rating.get("numRatings"),
                            instructor_id,
                        ),
                    )
                else:
                    cur.execute(
                        """INSERT INTO instructors(name,rmp_id,avg_rating,avg_difficulty,num_ratings,ratings_updated_at)
                        VALUES (%s,%s,%s,%s,%s,CASE WHEN %s IS NOT NULL THEN now() END) RETURNING id""",
                        (
                            instructor["name"],
                            rmp_id,
                            rating.get("avgRating"),
                            rating.get("avgDifficulty"),
                            rating.get("numRatings"),
                            rmp_id,
                        ),
                    )
                    row = cur.fetchone()
                    assert row is not None
                    instructor_id = row[0]
                cur.execute(
                    "INSERT INTO course_instructors VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (term_code, course["crn"], instructor_id),
                )
        cur.execute(
            "DELETE FROM instructors i WHERE NOT EXISTS (SELECT 1 FROM course_instructors ci WHERE ci.instructor_id=i.id)"
        )
        cur.execute(
            "UPDATE terms SET last_scraped_at=now() WHERE code=%s", (term_code,)
        )
