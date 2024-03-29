# Set variables
username=$SCHEDULER_DB_USERNAME
dbname=$SCHEDULER_DB_DBNAME
hostname=$SCHEDULER_DB_HOSTNAME
port=$SCHEDULER_DB_PORT
filename="src/create_tables.sql"

export PGPASSWORD=$SCHEDULER_DB_PG_PASSWORD
# Connect to PostgreSQL and execute SQL file
psql -U "$username" -h "$hostname" -p "$port" -d "$dbname" -f "$filename"
