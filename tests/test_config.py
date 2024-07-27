from drexel_scraper.config import Config
import pytest


@pytest.fixture
def config_args():
    return {
        "drexel_username": "abc123",
        "drexel_password": "mypassword",
        "output_file_name": "myfile.json",
        "mfa_secret_key": "hjkkkskskssksks",
        "term": "202415",
        "college_code": "CI",
        "include_ratings": True,
        "should_write_to_file": True,
        "should_write_to_db": True,
        "should_send_email_on_exception": True,
        "aws_topic_arn": "arn:aws:sns:us-east-1:123456789012:my-topic",
        "aws_sns_endpoint_url": None,
        "tms_base_url": "https://termmasterschedule.drexel.edu",
        "drexel_connect_base_url": "https://connect.drexel.edu",
    }


def test_config_with_valid_config(config_args):
    config = Config(**config_args)
    assert config.validate()
