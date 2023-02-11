from scrape import scrape

import json
import sys


def main():
    include_ratings = False
    if "--ratings" in sys.argv:
        include_ratings = True

    data = scrape(include_ratings=include_ratings)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Found {} items".format(len(data)))
    print("Data written to data.json")


if __name__ == "__main__":
    main()
