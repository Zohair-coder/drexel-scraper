import os

DBNAME = os.environ["SCHEDULER_DB_DBNAME"]
USER = os.environ["SCHEDULER_DB_USERNAME"]  # existing postgres user. change as needed
PASSWORD = os.environ["SCHEDULER_DB_PG_PASSWORD"]  # password for postgres user. change as needed
HOST = os.environ["SCHEDULER_DB_HOSTNAME"]  # default host for postgresql
PORT = os.environ["SCHEDULER_DB_PORT"]  # default port for postgresql
DEFAULT_DB = os.environ["SCHEDULER_DB_DEFAULT_DB"]  # default database for postgresql used to create the new database if it doesn't exist