from __future__ import annotations  # https://stackoverflow.com/a/49872353

import configargparse


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

    def validate(self) -> bool:
        return True

    def get_college_page_url(self, college_name: str) -> str:
        return self.tms_quarter_url + "?collCode=" + college_name
