# TMS-Scraper

Scrapes data from the Drexel term master schedule and outputs a JSON file.

Currently, the scraper only supports scraping the term master schedule for the summer term for the CCI college. You can, however, choose to modify these settings at your own risk by changing the `year`, `quarter`, and `college` variables in `config.py`.

## Installation

Make sure you have Python 3 installed. Then install requests and bs4.

```bash
pip3 install requests bs4
```

## Usage

To run the scraper, simply run the `python3 main.py` command. The scraper will output a JSON file called `data.json` in the same directory as the scraper.

To also include the ratings field in `data.json` that requests data from RateMyProfessor, run the following command:

```bash
python3 main.py --ratings
```

Note that this will take longer to run since the scraper has to look up the rating on ratemyprofessors. However, it will cache the ratings in a file called `ratings_cache` so that it doesn't have to look up the same professor again, which will run much faster. If you want to clear the cache to get new ratings, simply delete the `ratings_cache.json` file.

## Docker

Build the docker container by executing the following command:

```bash
docker build -t drexel-scraper .
```

To run the scraper in a Docker container, run the following command:

```bash
docker run -v $(pwd):/app drexel-scraper
```

Make sure you execute this in the project root directory. The scraper should then output the `data.json` file in the same directory.
