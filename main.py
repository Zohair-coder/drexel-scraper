from selenium import webdriver

from scrape import scrape

import json


def main():
    driver = webdriver.Chrome()
    data = scrape(driver)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Found {} items".format(len(data)))

    print("Data written to data.json")

    driver.close()


if __name__ == "__main__":
    main()
