# TMS-Scraper

Scrapes data from the Drexel term master schedule and outputs a JSON file. Note that this scraper is not officially supported by Drexel University, and may break if the term master schedule website changes.

## Installation

Make sure [git](https://git-scm.com/downloads) is installed. Clone the repository:

```bash
git clone https://github.com/Zohair-coder/drexel-scraper.git
cd drexel-scraper
```

Make sure you have [Python 3](https://www.python.org/downloads/). Then install the following packages:

```bash
pip3 install requests bs4
```

## Usage

To run the scraper, simply run the `python3 main.py` command. The scraper will output a JSON file called `data.json` in the same directory as the scraper.

You can modify the scraper to scrape other terms by changing the `year`, `quarter`, and `college_code` variables in `config.py`.

#### PostgreSQL

To add the data to a PostgreSQL database, make sure the [PostgreSQL](https://www.postgresql.org/download/) server is installed and running in the background. Check the settings in the db_config.py file. It is recommended that you set the necessary environment variables listed in the file, but if not it will use the defaults for Postgres. You can follow [this](https://phoenixnap.com/kb/windows-set-environment-variable) guide for Windows, and [this](https://phoenixnap.com/kb/set-environment-variable-mac) guide for MacOS to set environment variables. Install the psycopg2 package:

```bash
pip3 install  psycopg2-binary
```

And then run the scraper with the `--db` flag:

```bash
python3 main.py --db
```

This will create a new database `schedulerdb` and the necessary tables if they aren't already created, and then insert the data into the database. If the data is already populated, it will update the existing data. To delete all the data (e.g. for scraping another quarter's data), make sure the environment variables specified in `db_config.py` are set and then run the following command:

```
./reset_db.bash
```

To view the schema for the tables, you can look at the `create_tables.sql` file.

Connect to the database using the following command:

```bash
psql -U postgres schedulerdb
```

```sql
schedulerdb=# SELECT * FROM courses;
schedulerdb=# SELECT * FROM instructors;
schedulerdb=# SELECT * FROM course_instructor;
schedulerdb=# SELECT * FROM all_course_instructor_data;
```

I recommend viewing the data using another program like [pgAdmin](https://www.pgadmin.org/download/).

#### All Colleges

To scrape all colleges instead of just the one specified in the `config.json`, run the following command:

```bash
python3 main.py --all-colleges
```

#### Ratings

To also include the ratings field in `data.json` that requests data from RateMyProfessor, run the following command:

```bash
python3 main.py --ratings
```

Note that this will take longer to run since the scraper has to look up the rating on RateMyProfessors. However, it will cache the ratings in a file called `ratings_cache.json` so that it doesn't have to look up the same professor again, which will run much faster. If you want to clear the cache to get new ratings, simply delete the `ratings_cache.json` file.

You can also combine all the options together:

```bash
python3 main.py --db --all-colleges --ratings
```

## Docker

Build the docker container by executing the following command:

```bash
docker build -t drexel-scraper .
```

To run the scraper in a Docker container, run the following command:

```bash
docker run -v $(pwd):/app drexel-scraper
```

Make sure you execute this in the project root directory. The scraper should then output the `data.json` file in the same directory.
