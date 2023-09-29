import os

DBNAME = os.environ.get("SCHEDULER_DB_DBNAME", "schedulerdb") # name of the database to connect to
USER = os.environ.get("SCHEDULER_DB_USERNAME", "postgres")  # existing postgres user. change as needed
PASSWORD = os.environ.get("SCHEDULER_DB_PG_PASSWORD", "")  # password for postgres user. change as needed
HOST = os.environ.get("SCHEDULER_DB_HOSTNAME", "localhost")  # default host for postgresql
PORT = os.environ.get("SCHEDULER_DB_PORT", "5432")  # default port for postgresql
DEFAULT_DB = os.environ.get("SCHEDULER_DB_DEFAULT_DB", "postgres")  # default database for postgresql used to create the new database if it doesn't exist
GRAFANA_SERVICE_ACCOUNT_USERNAME = os.environ.get("SCHEDULER_DB_GRAFANA_SERVICE_ACCOUNT_USERNAME", "grafana") # grafana service account username that will read the data (will be created by script)
GRAFANA_SERVICE_ACCOUNT_PASSWORD = os.environ.get("SCHEDULER_DB_GRAFANA_SERVICE_ACCOUNT_PASSWORD", "super-strong-password") # grafana service account password