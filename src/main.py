from scrape import scrape

import json
import sys
import time
import os
import cProfile
import traceback
import argparse
import emailer
import db


def main(args: argparse.Namespace):
    start_time = time.time()

    data = scrape(include_ratings=args.ratings, all_colleges=args.all_colleges)

    assert len(data) > 0, "No data found"

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("Found {} items".format(len(data)))
    print("Data written to data.json")

    if args.db:
        print("Time taken to scrape data: {} seconds".format(time.time() - start_time))
        print()
        print("Updating database...")
        db.populate_db(data)

    print("Done!")

    print("--- {} seconds ---".format(time.time() - start_time))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape data from Term Master Schedule and save it to a data.json file."
    )
    parser.add_argument(
        "--ratings",
        action="store_true",
        help="Include Rate My Professor ratings in the data",
    )
    parser.add_argument(
        "--all-colleges",
        action="store_true",
        help="Include all colleges in the data, not just the one in the config.py file",
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="Update the database with the scraped data, or create a new one if it doesn't exist",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Send an email if an exception occurs (requires DREXEL_SCHEDULER_TOPIC_ARN environment variable to be set to the ARN of an AWS SNS topic)",
    )

    args = parser.parse_args()

    try:
        if not os.path.exists("performance"):
            os.makedirs("performance")
        cProfile.run("main(args)", "performance/profile_output.pstat")
    except Exception as e:
        trace = traceback.format_exc()
        print(trace)

        if args.email:
            environment = os.environ.get("ENVIRONMENT", "UNKNOWN")
            if emailer.send_email(f"{environment}: Error running scraper", trace):
                print("Exeception email sent")
            else:
                print("Error sending exception email")
        sys.exit(1)
