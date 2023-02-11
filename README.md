# TMS-Scraper

Scrapes data from the Drexel term master schedule and outputs a JSON file.

Currently, the scraper only supports scraping the term master schedule for the summer term for the CCI college.

## Installation

Make sure you have Python 3 installed. Then install bs4 and selenium. Installing selenium is a little more complex than simply running the `pip install selenium` command. You also have to download the web driver and make sure it matches with the current browser version. For a more detailed explanation, see [this](https://selenium-python.readthedocs.io/installation.html).

## Usage

To run the scraper, simply run the `python3 main.py` command. The scraper will output a JSON file called `data.json` in the same directory as the scraper.

To also include the ratings field in `data.json` that requests data from RateMyProfessor, run the following command:

```bash
python3 main.py --ratings
```

Note that this will take a lot longer to run.

## Docker

Build the docker container by executing the following command:

```bash
docker build -t drexel-scraper .
```

To run the scraper in a Docker container, run the following command:

```bash
docker run -v $(pwd):/app drexel-scraper
```

Make sure you execute this in the root directory. The scraper should then output the `data.json` file in the same directory.
