import os

class Config:
    def __init__(
        self,
        term: str,
        college_code: str | None,
        drexel_username: str | None,
        drexel_password: str | None,
        mfa_secret_key: str | None,
        include_ratings: bool,
        should_write_to_file: bool,
        should_write_to_db: bool,
        should_send_email_on_exception: bool,
        aws_topic_arn: str | None,
        aws_sns_endpoint_url: str | None,
    ):
        self.drexel_username = drexel_username or os.getenv("DREXEL_USERNAME")
        self.drexel_password = drexel_password or os.getenv("DREXEL_PASSWORD")
        self.drexel_mfa_secret_key = mfa_secret_key or os.getenv(
            "DREXEL_MFA_SECRET_KEY"
        )

        self.term = term
        self.college_code = college_code

        
        self.include_ratings = include_ratings
        self.should_write_to_file = should_write_to_file
        self.should_write_to_db = should_write_to_db
        self.should_send_email_on_exception = should_send_email_on_exception

        self.aws_topic_arn = aws_topic_arn
        self.aws_sns_endpoint_url = aws_sns_endpoint_url or os.getenv(
            "SNS_ENDPOINT_URL", None
        )

        self.tms_base_url = "https://termmasterschedule.drexel.edu"
        self.tms_home_url = self.tms_base_url + "/webtms_du"
        self.tms_quarter_url = self.tms_home_url + "/collegesSubjects/" + self.term
        self.drexel_connect_base_url = "https://connect.drexel.edu"


    def get_college_page_url(self, college_name: str) -> str:
        return self.tms_quarter_url + "?collCode=" + college_name
