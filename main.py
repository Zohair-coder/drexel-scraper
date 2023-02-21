from scrape import scrape

import json
import sys
import db


def main():
    include_ratings = False
    if "--ratings" in sys.argv:
        include_ratings = True

    all_colleges = False
    if "--all-colleges" in sys.argv:
        all_colleges = True

    data = scrape(include_ratings=include_ratings, all_colleges=all_colleges)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Found {} items".format(len(data)))
    print("Data written to data.json")

    if "--db" in sys.argv:
        print("Updating database...")
        db.populate_db(data)

    print("Done!")


if __name__ == "__main__":
    main()
