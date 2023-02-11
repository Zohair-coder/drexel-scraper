from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scrape import scrape

import json

import sys


def main():
    options = Options()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    include_ratings = False
    if "--ratings" in sys.argv:
        include_ratings = True

    data = scrape(driver, include_ratings)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Found {} items".format(len(data)))
    print("Data written to data.json")

    driver.close()


if __name__ == "__main__":
    main()
