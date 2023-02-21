#!/bin/bash

# Set variables
username="postgres"
dbname="schedulerdb"
filename="create_tables.sql"

# Connect to PostgreSQL and execute SQL file
psql -U "$username" -d "$dbname" -f "$filename"
