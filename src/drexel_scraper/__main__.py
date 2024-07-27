from __future__ import annotations  # https://stackoverflow.com/a/49872353

import json
import os
import sys
import time
import traceback

import configargparse

from drexel_scraper import db, emailer
from drexel_scraper.config import Config
from drexel_scraper.scrape import scrape


def main() -> None:
    parser = configargparse.ArgumentParser(
            prog="drexelscraper",
            description="Scrape data from Drexel Term Master Schedule and save it to a JSON file.",
            )
    parser.add_argument(
            "-u",
            "--username",
            action="store",
            env_var="DS_DREXEL_USERNAME",
            help="DrexelOne abc123 username (without @drexel.edu).",
            required=True,
            )
    #TODO: find a way to hide the password when typing it in
    parser.add_argument(
            "-p",
            "--password",
            action="store",
            env_var="DS_DREXEL_PASSWORD",
            help="DrexelOne password.",
            required=True,
            )
    parser.add_argument(
            "-o",
            "--output-file",
            metavar="FILE",
            action="store",
            env_var="DS_OUTPUT_FILE",
            default="data.json",
            help="File to write the data to (include the .json extension in the file name).",
            )
    parser.add_argument(
            "-m",
            "--mfa-secret",
            action="store",
            env_var="DS_DREXEL_MFA_SECRET_KEY",
            help="DrexelOne MFA secret key (https://github.com/Zohair-coder/drexel-scraper?tab=readme-ov-file#authenticate-using-a-secret-key).",
            )
    parser.add_argument(
            "-t",
            "--term",
            action="store",
            env_var="DS_TERM",
            default="202415",
            help="Term to scrape (e.g. '202415' for Fall 2024). Follows the format 'YYYYTT', where YYYY is the year and TT is the term code (15 for Fall, 25 for Winter, 35 for Spring, 45 for Summer).",
            )
    parser.add_argument(
            "-c",
            "--college",
            action="store",
            env_var="DS_COLLEGE",
            default=None,
            help="Specify a college to scrape (e.g. 'CI' for CCI) instead of scraping all colleges. You can find the college code by going to the TMS website (https://termmasterschedule.drexel.edu/) and selecting your college from the left sidebar. The URL bar should update and it should end with something like collCode=CI. The characters after the = sign is your college code.",
            ),
    parser.add_argument(
            "--exclude-ratings",
            action="store_true",
            env_var="DS_EXCLUDE_RATINGS",
            help="Do not include Rate My Professor ratings in the data.",
            )
    parser.add_argument(
            "--no-file",
            action="store_true",
            env_var="DS_NO_FILE",
            help="Do not write the data to a file.",
            )
    parser.add_argument(
            "--db",
            action="store_true",
            env_var="DS_DB",
            help="Update the database with the scraped data, or create a new one if it doesn't exist.",
            )
    parser.add_argument(
            "--email",
            action="store_true",
            env_var="DS_EMAIL",
            help="Send an email if an exception occurs (requires --aws-topic-arn to be set).",
            )
    parser.add_argument(
            "--aws-topic-arn",
            action="store",
            env_var="DS_AWS_TOPIC_ARN",
            help="ARN of the AWS SNS topic to use for sending emails.",
            )
    parser.add_argument(
            "--aws-sns-endpoint-url",
            action="store",
            env_var="DS_AWS_SNS_ENDPOINT_URL",
            help="URL of the AWS SNS endpoint to use for sending emails.",
            )
    parser.add_argument(
            "--tms-base-url",
            action="store",
            env_var="DS_TMS_BASE_URL",
            default="https://termmasterschedule.drexel.edu",
            help=configargparse.SUPPRESS,
            )
    parser.add_argument(
            "--drexel_connect_base_url",
            action="store",
            env_var="DS_DREXEL_CONNECT_BASE_URL",
            default="https://connect.drexel.edu",
            help=configargparse.SUPPRESS,
            )

    args = parser.parse_args()
    config = Config.generate_config_from_args(args)
    config.validate()

    try:
        start(config)
    except Exception:
        trace = traceback.format_exc()
        print(trace)

        if config.should_send_email_on_exception:
            environment = os.environ.get("ENVIRONMENT", "UNKNOWN")
            if emailer.send_email(f"{environment}: Error running scraper", trace):
                print("Exeception email sent")
            else:
                print("Error sending exception email")
        sys.exit(1)

def start(config: Config) -> None:
    start_time = time.time()

    data = scrape(config)

    assert len(data) > 0, "No data found"
    print(f"Found {len(data)} items")

    if config.should_write_to_file:
        with open(config.output_file_name, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Data written to {config.output_file_name}")

    if config.should_write_to_db:
        print(f"Time taken to scrape data: {time.time() - start_time} seconds")
        print()
        print("Updating database...")
        db.populate_db(data)
        print("Done!")

    print(f"--- {time.time() - start_time} seconds ---")


if __name__ == "__main__":
    main()
