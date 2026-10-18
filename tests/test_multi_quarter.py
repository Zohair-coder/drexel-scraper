"""Real PostgreSQL integration tests; set TEST_DATABASE_DSN to a disposable *_test DB."""

import copy
import json
import os
from pathlib import Path
import sys

import psycopg2
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import db
from terms import discover_terms, term_label


def test_catalogue():
    html = '<a href="/webtms_du/collegesSubjects/202625?collCode=">Winter Quarter 26-27</a><a href="/webtms_du/collegesSubjects/202611">Fall Semester</a>'
    assert discover_terms(html) == {"202625": "Winter 2027"}
    assert term_label("202615") == "Fall 2026"
    with pytest.raises(ValueError):
        discover_terms("Sign in")


@pytest.fixture
def database(monkeypatch):
    dsn = os.getenv("TEST_DATABASE_DSN")
    if not dsn:
        pytest.skip("TEST_DATABASE_DSN not configured")
    conn = psycopg2.connect(dsn)
    assert conn.info.dbname.endswith("_test"), "Only disposable test databases allowed"
    with conn, conn.cursor() as cur:
        cur.execute(
            "DROP SCHEMA IF EXISTS legacy_single_quarter CASCADE; DROP SCHEMA public CASCADE; CREATE SCHEMA public"
        )
    conn.close()

    def connect():
        connection = psycopg2.connect(dsn)
        return connection.cursor(), connection

    monkeypatch.setattr(db, "connect_to_db", connect)
    return connect


def seed_schema(database):
    cur, conn = database()
    with conn, cur:
        db.create_tables(cur)
    conn.close()


def course(name="One Professor", rmp=123):
    return {
        "12345": {
            "crn": 12345,
            "subject_code": "CS",
            "course_number": "101",
            "course_title": "Intro",
            "section": "001",
            "instruction_type": "Lecture",
            "instruction_method": "Face To Face",
            "enroll": "FULL",
            "max_enroll": "FULL",
            "credits": "3",
            "prereqs": "",
            "start_time": None,
            "end_time": None,
            "days": None,
            "college_code": "CI",
            "instructors": [
                {
                    "name": name,
                    "rating": {
                        "legacyId": rmp,
                        "avgRating": 4,
                        "avgDifficulty": 3,
                        "numRatings": 10,
                    }
                    if rmp
                    else None,
                }
            ],
        }
    }


def rows(database, query):
    cur, conn = database()
    with conn, cur:
        cur.execute(query)
        result = cur.fetchall()
    conn.close()
    return result


def test_refresh_isolation_and_rollback(database):
    seed_schema(database)
    db.populate_db(course(), "202615")
    db.populate_db(course("Other Professor", 456), "202625")
    before = rows(database, "SELECT * FROM terms ORDER BY code")
    invalid = course()
    invalid["12345"]["days"] = "invalid-array"
    with pytest.raises(psycopg2.Error):
        db.populate_db(invalid, "202615")
    assert rows(database, "SELECT * FROM terms ORDER BY code") == before
    assert rows(
        database,
        "SELECT term_code,instructor_name FROM all_course_instructor_data ORDER BY term_code",
    ) == [("202615", "One Professor"), ("202625", "Other Professor")]
    db.populate_db(course("Replacement", 789), "202615")
    assert rows(
        database,
        "SELECT term_code,instructor_name FROM all_course_instructor_data ORDER BY term_code",
    ) == [("202615", "Replacement"), ("202625", "Other Professor")]
    with pytest.raises(ValueError):
        db.populate_db({}, "202625")


def test_same_name_different_identities_and_unassigned(database):
    seed_schema(database)
    data = course("Same Name", 123)
    second = copy.deepcopy(data["12345"])
    second["crn"] = 12346
    second["instructors"][0]["rating"]["legacyId"] = 456
    data["12346"] = second
    third = copy.deepcopy(second)
    third["crn"] = 12347
    third["instructors"] = None
    data["12347"] = third
    db.populate_db(data, "202615")
    assert rows(database, "SELECT count(*) FROM instructors") == [(2,)]
    assert rows(database, "SELECT count(*) FROM all_course_instructor_data") == [(3,)]


def test_dashboard_queries(database):
    seed_schema(database)
    db.populate_db(course(), "202615")
    db.populate_db(course("Winter Professor", 456), "202625")
    path = (
        Path(__file__).resolve().parents[1]
        / "k8s/drexel-scraper/dashboards/scheduler.json"
    )
    dashboard = json.loads(path.read_text())
    defaults = {
        v["name"]: v["current"].get("value", "")
        for v in dashboard["templating"]["list"]
    }
    quarter = next(v for v in dashboard["templating"]["list"] if v["name"] == "quarter")
    assert len(rows(database, quarter["query"])) == 2
    for code in ("202615", "202625"):
        for panel in dashboard["panels"]:
            for target in panel.get("targets", []):
                query = target["rawSql"].replace(
                    "${quarter:sqlstring}", "'" + code + "'"
                )
                for key, value in defaults.items():
                    query = query.replace("$" + key, str(value))
                result = rows(database, query)
                if panel["id"] in (2, 3):
                    assert result == [(1,)]


def test_legacy_migration_is_preserving_and_idempotent(database):
    cur, conn = database()
    with conn, cur:
        cur.execute("""CREATE TABLE metadata(key text PRIMARY KEY,value text);
            INSERT INTO metadata VALUES ('current_year','2026'),('current_quarter','25');
            CREATE TABLE instructors(id serial PRIMARY KEY,name text UNIQUE,rmp_id integer,avg_rating numeric,avg_difficulty numeric,num_ratings integer);
            INSERT INTO instructors(name,rmp_id) VALUES ('Legacy Professor',123);
            CREATE TABLE courses(crn integer PRIMARY KEY,subject_code text,course_number text,course_title text,section text,instruction_type text,instruction_method text,enroll text,max_enroll text,credits text,prereqs text,start_time time,end_time time,days text[]);
            INSERT INTO courses VALUES (12345,'CS','101','Intro','001','Lecture','Online','FULL','FULL','3','',NULL,NULL,NULL);
            CREATE TABLE course_instructor(course_id integer REFERENCES courses(crn),instructor_id integer REFERENCES instructors(id),PRIMARY KEY(course_id,instructor_id));
            INSERT INTO course_instructor VALUES(12345,1);
            CREATE VIEW all_course_instructor_data AS SELECT * FROM courses;
        """)
        db.create_tables(cur)
        db.create_tables(cur)
    conn.close()
    assert rows(
        database,
        "SELECT term_code,instructor_name,enroll FROM all_course_instructor_data",
    ) == [("202625", "Legacy Professor", "FULL")]
    assert rows(database, "SELECT count(*) FROM legacy_single_quarter.courses") == [
        (1,)
    ]
    assert rows(database, "SELECT label FROM terms") == [("Winter 2027",)]
    db.populate_db(course("New Professor", 456), "202615")
    assert rows(database, "SELECT count(*) FROM courses") == [(2,)]
