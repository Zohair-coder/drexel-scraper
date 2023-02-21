DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS instructors CASCADE;
DROP TABLE IF EXISTS course_instructor CASCADE;

CREATE TABLE instructors (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
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
