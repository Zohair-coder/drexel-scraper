FROM python:3.10-alpine

# set the working directory in the container
WORKDIR /app

# copy the current directory contents into the container at /app
COPY . /app

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

# install chromedriver
RUN apk update
RUN apk add chromium=109.0.5414.74-r0 chromium-chromedriver=109.0.5414.74-r0

# upgrade pip
RUN pip install --upgrade pip

# install selenium and BeautifulSoup
RUN pip install selenium bs4

# Run the Python script
CMD ["python", "main.py"]
