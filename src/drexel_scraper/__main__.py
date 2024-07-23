from drexel_scraper.scrape import scrape
import drexel_scraper.emailer as emailer
import drexel_scraper.db as db

import json
import sys
import time
import os
import traceback
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python3 src/main.py",
        description="Scrape data from Drexel Term Master Schedule and save it to a JSON file."
    )
    parser.add_argument(
        "-o",
        "--output-file",
        metavar="FILE",
        action="store",
        default="data.json",
        help="File to write the data to (include the .json extension in the file name)",
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
        "--no-file",
        action="store_true",
        help="Do not write the data to a file",
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
        start(args)
    except Exception:
        trace = traceback.format_exc()
        print(trace)

        if args.email:
            environment = os.environ.get("ENVIRONMENT", "UNKNOWN")
            if emailer.send_email(f"{environment}: Error running scraper", trace):
                print("Exeception email sent")
            else:
                print("Error sending exception email")
        sys.exit(1)

def start(args: argparse.Namespace) -> None:
    start_time = time.time()

    data = scrape(include_ratings=args.ratings, all_colleges=args.all_colleges)

    assert len(data) > 0, "No data found"
    print("Found {} items".format(len(data)))

    if not args.no_file:
        with open(args.output_file, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Data written to {args.output_file}")

    if args.db:
        print("Time taken to scrape data: {} seconds".format(time.time() - start_time))
        print()
        print("Updating database...")
        db.populate_db(data)
        print("Done!")

    print("--- {} seconds ---".format(time.time() - start_time))

if __name__ == "__main__":
    main()