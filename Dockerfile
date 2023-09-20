FROM python:3.10-alpine

# set the working directory in the container
WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app

# upgrade pip
RUN pip install --upgrade pip

# install dependencies
RUN pip install bs4 requests psycopg2-binary

# Run the Python script
CMD ["python", "main.py", "--db", "--all-colleges", "--ratings"]