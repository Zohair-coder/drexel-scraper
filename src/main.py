from scrape import scrape, authenticated_session
from helpers import send_request
from terms import BASE, discover_terms
import config

import json
import sys
import time
import os
import cProfile
import traceback
import argparse
import emailer
import db


def main(args: argparse.Namespace) -> None:
    start_time = time.time()

    if args.db or args.migrate_only:
        db.initialize(config.year + config.quarter)
    if args.migrate_only:
        print("Database migration complete")
        return
    session = authenticated_session()
    catalogue = discover_terms(send_request(session, BASE).text)
    if args.db:
        db.update_catalogue(catalogue, config.year + config.quarter)
    selected = (
        list(catalogue)
        if args.all_quarters
        else [args.term or config.year + config.quarter]
    )
    if any(code not in catalogue for code in selected):
        raise ValueError("Requested quarter is not advertised by TMS")
    failures = []
    for term_index, code in enumerate(selected, start=1):
        print(
            f"Scraping {catalogue[code]} ({code}) ({term_index}/{len(selected)})",
            flush=True,
        )
        try:
            data = scrape(
                include_ratings=args.ratings,
                all_colleges=args.all_colleges,
                term_code=code,
                session=session,
                term_index=term_index,
                term_count=len(selected),
            )
            if not data:
                raise ValueError(f"No data for {code}; retaining existing quarter")
            print(f"Found {len(data)} sections for {code}", flush=True)
            if not args.no_file:
                filename = (
                    f"{os.path.splitext(args.output_file)[0]}-{code}.json"
                    if args.all_quarters
                    else args.output_file
                )
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
            if args.db:
                db.populate_db(data, code)
                print(f"Published {code}", flush=True)
        except Exception as exc:
            if not args.all_quarters:
                raise
            # Exception messages can include upstream response headers or bodies.
            # Report the quarter and exception type without leaking those details.
            print(
                f"Failed {code} ({type(exc).__name__}); continuing with remaining quarters",
                flush=True,
            )
            failures.append(code)

    if failures:
        raise RuntimeError(f"Quarters failed: {', '.join(failures)}")

    print("--- {} seconds ---".format(time.time() - start_time))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="python3 src/main.py",
        description="Scrape data from Drexel Term Master Schedule and save it to a JSON file.",
    )
    quarters = parser.add_mutually_exclusive_group()
    quarters.add_argument(
        "--all-quarters",
        action="store_true",
        help="Collect every quarter currently advertised by TMS",
    )
    quarters.add_argument("--term", help="Collect one TMS quarter code, e.g. 202625")
    parser.add_argument(
        "--migrate-only",
        action="store_true",
        help="Initialize/migrate the database without scraping",
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
        if not os.path.exists("performance"):
            os.makedirs("performance")
        cProfile.run("main(args)", "performance/profile_output.pstat")
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
