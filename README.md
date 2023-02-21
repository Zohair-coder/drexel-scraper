# TMS-Scraper

Scrapes data from the Drexel term master schedule and outputs a JSON file.

Currently, the scraper only supports scraping the term master schedule for the summer term for the CCI college. You can, however, choose to modify these settings at your own risk by changing the `year`, `quarter`, and `college` variables in `config.py`.

## Installation

Make sure you have Python 3 installed. Then install requests and bs4.

```bash
pip3 install requests bs4
```

## Usage

To run the scraper, simply run the `python3 main.py` command. The scraper will output a JSON file called `data.json` in the same directory as the scraper.

You can modify the scraper to scrape other terms by changing the `year`, `quarter`, and `college_code` variables in `config.py`.

#### PostgreSQL

To add the data to a PostgreSQL database, make sure a PostgreSQL server is running in the background and then run the following command:

```bash
python3 main.py --db
```

This will create a new database `schedulerdb` and the necessary tables if they aren't already created, and then insert the data into the database. If the data is already populated, it will update the existing data. It won't delete any data, it will only update it. To delete all the data, you can run the following command:

```
./reset_db.sh
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
```

I recommend viewing the data using another program like pgAdmin.

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

Note that this will take longer to run since the scraper has to look up the rating on ratemyprofessors. However, it will cache the ratings in a file called `ratings_cache` so that it doesn't have to look up the same professor again, which will run much faster. If you want to clear the cache to get new ratings, simply delete the `ratings_cache.json` file.

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
