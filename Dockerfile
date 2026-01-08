FROM python:3.12

# set the working directory in the container
WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app

# install dependencies
# Pre-install fonts that playwright expects (package names changed in newer Debian)
RUN apt-get update && apt-get install -y \
    fonts-unifont \
    fonts-ubuntu \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install chromium --with-deps

# Run the Python script
CMD ["python3", "src/main.py", "--db", "--all-colleges", "--ratings", "--email"]