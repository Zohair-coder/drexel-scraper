DROP VIEW IF EXISTS all_course_instructor_data;
DROP TABLE IF EXISTS course_instructor CASCADE;
DROP TABLE IF EXISTS instructors CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS metadata;

CREATE TABLE metadata (
    key VARCHAR(255) NOT NULL,
    value TEXT,
    PRIMARY KEY (key)
);

CREATE TABLE instructors (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    avg_difficulty  NUMERIC,
    avg_rating      NUMERIC,
    num_ratings     INTEGER
);

CREATE TABLE courses
(
	crn          	    INTEGER PRIMARY KEY,
	subject_code        TEXT NOT NULL,
	course_number       TEXT NOT NULL,
    instruction_type    TEXT NOT NULL,
    instruction_method  TEXT NOT NULL,
    section             TEXT NOT NULL,
    enroll              TEXT,
    max_enroll          TEXT,
    course_title        TEXT NOT NULL,
    credits             REAL,
    start_time          TIME,
    end_time            TIME,
    days                TEXT[]
);

CREATE TABLE course_instructor
(
    course_id           INTEGER REFERENCES courses(crn),
    instructor_id       INTEGER REFERENCES instructors(id),
    PRIMARY KEY (course_id, instructor_id)
);

CREATE VIEW all_course_instructor_data AS
SELECT 
    i.id AS instructor_id,
    i.name AS instructor_name,
    i.avg_difficulty,
    i.avg_rating,
    i.num_ratings,
    c.crn AS course_id,
    c.subject_code,
    c.course_number,
    c.instruction_type,
    c.instruction_method,
    c.section,
    c.enroll,
    c.max_enroll,
    c.course_title,
    c.credits,
    c.start_time,
    c.end_time,
    c.days
FROM instructors i
JOIN course_instructor ci ON i.id = ci.instructor_id
JOIN courses c ON ci.course_id = c.crn;
