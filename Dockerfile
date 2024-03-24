FROM python:3.12-alpine

# set the working directory in the container
WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app

# upgrade pip
RUN pip install --upgrade pip

# install dependencies
RUN pip install -r requirements.txt

# Run the Python script
CMD ["python3", "src/main.py", "--db", "--all-colleges", "--ratings", "--email"]