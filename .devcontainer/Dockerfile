FROM mcr.microsoft.com/devcontainers/python

# set the working directory in the container
WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app

# upgrade pip
RUN pip install --upgrade pip

# install dependencies
RUN pip install -r requirements.txt

# only for dev container
RUN apt-get update && apt-get install -y postgresql-client

# Run the Python script
CMD ["python3", "src/main.py", "--db", "--all-colleges", "--ratings", "--email"]