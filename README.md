UI for data: https://scheduler.zohair.dev

# TMS-Scraper

Scrapes data from the Drexel Term Master Schedule and outputs a JSON file. Note that this scraper is not officially supported by Drexel University, and may break if the term master schedule website changes.

## Installation

Make sure [git](https://git-scm.com/downloads) is installed. Clone the repository:

```bash
git clone https://github.com/Zohair-coder/drexel-scraper.git
cd drexel-scraper
```

Make sure you have [Python 3](https://www.python.org/downloads/) installed. Then install the dependencies by running the following command:

###### Mac/Linux
```bash
pip3 install -r requirements.txt
playwright install
```

###### Windows
```bash
pip install -r requirements.txt
playwright install
```

## Usage

First, [set up authentication](#Authentication).
Then, to run the scraper, simply run:

###### Mac/Linux
```bash
python3 src/main.py
```

###### Windows
```bash
python src/main.py
```

The scraper will output a JSON file called `data.json` in the same directory as the scraper.

You can modify the scraper to scrape other terms by changing the `year`, `quarter`, and `college_code` variables in `src/config.py`.

To view all the options that the scraper supports, run `python3 src/main.py --help` on Mac/Linux, or `python src/main.py --help` on Windows.  

#### Authentication

Since the term master schedule is only accessible to logged-in Drexel students, to run the scraper, you will need to provide your Drexel credentials as well as provide multi-factor authentication (MFA).

To provide your Drexel credentials, set the environment variable `DREXEL_EMAIL` to your Drexel email (abc123@drexel.edu) and `DREXEL_PASSWORD` to the password you use to login to Drexel One. You can follow [this](https://phoenixnap.com/kb/windows-set-environment-variable) guide for Windows, and [this](https://phoenixnap.com/kb/set-environment-variable-mac) guide for MacOS to set environment variables.

You will also need to go to [this page](https://mysignins.microsoft.com/security-info) and make sure "Authenticator app or hardware token" is the preferred sign-in method. Unfortunately, if you use Microsoft Authenticator as your MFA app you will not be able to run the scraper. You will have to delete the Microsoft Authenticator sign in method and install a different MFA app. 

There are two ways to provide MFA for the script to authenticate with. The first is easier if you're looking to run the script manually and quickly. The second is better if you are going to be running the script frequently, or if it needs to be automated.

###### Authenticate manually

You will authenticate the scraper manually as if you were logging into Drexel One, using a one-time code either from an authenticator app or that is texted to you. After setting the `DREXEL_EMAIL` and `DREXEL_PASSWORD` environment variables, run the scraper as explained [above](#Usage), and you will be prompted for your verification code.

###### Authenticate using a secret key

If you set this up, you will not need to manually enter an authentication code each time you run the scraper. 

1. Go to [connect.drexel.edu](connect.drexel.edu). 
2. Click 'Help & Settings', then 'Change MFA settings'.
3. Log in to the Microsoft portal, then click 'Add sign-in method' on the 'Security info' tab.
4. Select 'Authenticator app' for the method, and click 'Add'.
5. Select 'I want to use a different authenticator app', and then 'Next'.
6. Select 'Can't scan image?' when prompted with a QR code, and you should see an Account name and Secret key.
7. Set your `DREXEL_MFA_SECRET_KEY` environment variable to the given Secret key.
8. Select 'Next', you should be prompted to enter an authentication code.
9. With the secret key environment variable set, run `python3 src/totp.py` which will generate a one-time code.
10. Enter this code into the Microsoft website, and select 'Next'
11. 'Authenticator app' with TOTP should have been added to the list of available methods.

Now, when you run the scraper as explained [above](#Usage), it should authenticate itself automatically using this secret key.

#### All Colleges

To scrape all colleges instead of just the one specified in the `src/config.py`, run the following command:

###### Mac/Linux
```bash
python3 src/main.py --all-colleges
```

###### Windows
```bash
python src/main.py --all-colleges
```

#### Ratings

To also include the ratings field in `data.json` that requests data from RateMyProfessor, run the following command:

###### Mac/Linux
```bash
python3 src/main.py --ratings
```

###### Windows
```bash
python src/main.py --ratings
```

Note that this will take longer to run since the scraper has to look up the rating on RateMyProfessors. However, it will cache the ratings in a file called `ratings_cache.json` (inside the `cache` directory) so that it doesn't have to look up the same professor again, which will run much faster. If you want to clear the cache to get new ratings, simply delete the `ratings_cache.json` file.

#### PostgreSQL

To add the data to a PostgreSQL database, make sure the [PostgreSQL](https://www.postgresql.org/download/) server is installed and running in the background. Check the settings in the db_config.py file. It is recommended that you set the necessary environment variables listed in the file, but if not, it will use the defaults for Postgres. You can follow [this](https://phoenixnap.com/kb/windows-set-environment-variable) guide for Windows, and [this](https://phoenixnap.com/kb/set-environment-variable-mac) guide for MacOS to set environment variables.

Then run the scraper with the `--db` flag:

###### Mac/Linux
```bash
python3 src/main.py --db
```

###### Windows
```bash
python src/main.py --db
```

This will create a new database `schedulerdb` and the necessary tables if they aren't already created, and then insert the data into the database. If the data is already populated, it will update the existing data. To delete all the data, make sure the environment variables specified in `src/db_config.py` are set and then run the following command (make sure you're using the Git Bash terminal if you're using Windows):

```bash
./scripts/reset-db.sh
```

To view the schema for the tables, you can look at the `src/create_tables.sql` file.

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

You can also combine all the options together:

###### Mac/Linux
```bash
python3 src/main.py --db --all-colleges --ratings
```

###### Windows
```bash
python src/main.py --db --all-colleges --ratings
```

## Docker

You can also run the scraper in a Docker container. Make sure [Docker](https://docs.docker.com/get-docker/) is installed. You can then either open up the folder in VS Code as a Dev Container (preferred), or run the following command to run it:

```bash
docker compose up -d --build
```

Make sure you execute this in the project root directory. Let the scraper container finish/exit. The scraper should then output the `data.json` file in the same directory. You can view the data inside the database by going to `http://localhost:30012` in your browser.

You can also view a Grafana instance by going to `http://localhost:3000`. You will have to log in with the username `admin` and password `admin`. The first time you log in, you will have to set up the datasource and dashboard. To set up the datasource, click the sidebar menu and go to `Connections -> Data Sources -> Add new data source` and search for `PostgreSQL`. Enter in the following information:

```
Host: postgres
Database: postgres
User: postgres
Password: super-secret-password
TLS/SSL Mode: disable
```

And then click `Save and test`.

You will also have to import the dashboard at [schedulerdev.zohair.dev](https://schedulerdev.zohair.dev). Click the share icon at the top and then go to the export tab. Check the "Export for sharing externally" box and then click "Save to file". You can then import this dashboard by going to `Home > Dashboards` on your local Grafana instance and then clicking `New > Import`. Upload the file you just downloaded and everything should be set up.

To run the script again after the container has exited, run the following command:

```bash
docker compose up -d
```

To delete the containers, run the following command:

```bash
docker compose down
```

If you want to reset the database, delete the postgres-data directory inside the project root directory.

If you want to reset the Grafana settings, delete the grafana_data directory inside the project root directory.

NOTE: Docker Compose is only used for local development. The production version of the scraper uses Kubernetes. The Kubernetes configuration files live in the `k8s` directory.

## Contributing

If you wish to contribute, please take a look at the "Issues" tab and see if there are any issues you can help with. If you wish to add/request a new feature, you can create a new issue, and we can talk about it there before you start working on it. If you wish to work on an existing issue, please comment on the issue so that I can assign it to you. Once you have completed the issue, you can create a pull request to the dev branch, and I will review it. After merging the changes to the dev branch, the job will be deployed on the dev server (https://schedulerdev.zohair.dev). If there are no issues, I will merge the changes to the main branch, and the job will be deployed on the main server (https://scheduler.zohair.dev).

If you want to contact me directly, you can email me at zohair.ul.hasan@gmail.com.
