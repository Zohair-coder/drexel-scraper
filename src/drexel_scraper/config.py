from __future__ import annotations  # https://stackoverflow.com/a/49872353
import os

from .models.result import Result

import configargparse
from getpass import getpass


class Config:
    def __init__(
            self,
            drexel_username: str | None,
            drexel_password: str | None,
            output_file_name: str | None,
            term: str,
            college_code: str | None,
            mfa_secret_key: str | None,
            include_ratings: bool,
            should_write_to_file: bool,
            should_write_to_db: bool,
            should_send_email_on_exception: bool,
            aws_topic_arn: str | None,
            aws_sns_endpoint_url: str | None,
            tms_base_url: str,
            drexel_connect_base_url: str,
            ):
        self.drexel_username = drexel_username
        self.drexel_password = drexel_password
        self.drexel_mfa_secret_key = mfa_secret_key

        self.term = term
        self.college_code = college_code

        self.output_file_name = output_file_name

        self.include_ratings = include_ratings
        self.should_write_to_file = should_write_to_file
        self.should_write_to_db = should_write_to_db
        self.should_send_email_on_exception = should_send_email_on_exception

        self.aws_topic_arn = aws_topic_arn
        self.aws_sns_endpoint_url = aws_sns_endpoint_url

        self.tms_base_url = tms_base_url
        self.tms_home_url = self.tms_base_url + "/webtms_du"
        self.tms_quarter_url = self.tms_home_url + "/collegesSubjects/" + self.term
        self.drexel_connect_base_url = drexel_connect_base_url

    @staticmethod
    def generate_config_from_args(args: configargparse.Namespace) -> Config:
        if not args.username:
            args.username = input("Drexel username (abc123): ")

        if not args.password:
            args.password = getpass("Drexel password: ")
        
        return Config(
            drexel_username=args.username,
            drexel_password=args.password,
            output_file_name=args.output_file,
            mfa_secret_key=args.mfa_secret,
            term=args.term,
            college_code=args.college,
            include_ratings=not args.exclude_ratings,
            should_write_to_file=not args.no_file,
            should_write_to_db=args.db,
            should_send_email_on_exception=args.email,
            aws_topic_arn=args.aws_topic_arn,
            aws_sns_endpoint_url=args.aws_sns_endpoint_url,
            tms_base_url=args.tms_base_url,
            drexel_connect_base_url=args.drexel_connect_base_url,
        )

    def validate(self) -> Result:
        errors = []
        
        if not self.drexel_username or self.drexel_username == "":
            errors.append("Drexel username is required")
        
        if not self.drexel_password or self.drexel_password == "":
            errors.append("Drexel password is required")
            
        if self.should_write_to_file and (not self.output_file_name or self.output_file_name == ""):
            errors.append("Output file name is required")
        
        if self.term is None or len(self.term) != 6:
            errors.append("Term is required and must be in the format YYYYTT")
            
        if self.should_send_email_on_exception and (not self.aws_topic_arn or self.aws_topic_arn == ""):
            errors.append("AWS SNS Topic ARN is required to send emails")
        
        if self.should_send_email_on_exception and (not os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_DEFAULT_REGION") == ""):
            errors.append("AWS_DEFAULT_REGION ennvironment variable is required to send emails")
        
        if self.should_send_email_on_exception and (not os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID") == ""):
            errors.append("AWS_ACCESS_KEY_ID ennvironment variable is required to send emails")
        
        if self.should_send_email_on_exception and (not os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY") == ""):
            errors.append("AWS_SECRET_ACCESS_KEY ennvironment variable is required to send emails")

        return Result(ok=len(errors) == 0, errors=errors)

    def get_college_page_url(self, college_name: str) -> str:
        return self.tms_quarter_url + "?collCode=" + college_name