from drexel_scraper.config import Config
import pytest

@pytest.fixture
def config_args(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "myaccesskey")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "mysecret")
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
        "should_send_email_on_exception": False,
        "aws_topic_arn": None,
        "aws_sns_endpoint_url": None,
        "tms_base_url": "https://termmasterschedule.drexel.edu",
        "drexel_connect_base_url": "https://connect.drexel.edu",
    }


def test_config_with_valid_config(config_args):
    config = Config(**config_args)
    result = config.validate()
    assert result.ok
    assert not result.errors

def test_config_with_invalid_username(config_args):
    config_args["drexel_username"] = None
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_empty_username(config_args):
    config_args["drexel_username"] = ""
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_invalid_password(config_args):
    config_args["drexel_password"] = None
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_empty_password(config_args):
    config_args["drexel_password"] = ""
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_invalid_term(config_args):
    config_args["term"] = "2024"
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_send_email_on_exception_without_topic_arn(config_args, monkeypatch):
    config_args["should_send_email_on_exception"] = True

    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_send_email_on_exception_without_aws_default_region(config_args, monkeypatch):
    config_args["should_send_email_on_exception"] = True
    config_args["aws_topic_arn"] = "arn:aws:sns:us-east-1:123456789012:MyTopic"

    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_send_email_on_exception_without_access_key_id(config_args, monkeypatch):
    config_args["should_send_email_on_exception"] = True
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "mysecret")
    config_args["aws_topic_arn"] = "arn:aws:sns:us-east-1:123456789012:MyTopic"

    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)

    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_send_email_on_exception_without_secret_access_key(config_args, monkeypatch):
    config_args["should_send_email_on_exception"] = True
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "mysecret")
    config_args["aws_topic_arn"] = "arn:aws:sns:us-east-1:123456789012:MyTopic"

    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_send_email_on_exception_with_all_values(config_args):
    config_args["should_send_email_on_exception"] = True
    config_args["aws_topic_arn"] = "arn:aws:sns:us-east-1:123456789012:MyTopic"

    config = Config(**config_args)
    result = config.validate()
    assert result.ok
    assert not result.errors
    
def test_config_with_none_tms_base_url(config_args):
    config_args["tms_base_url"] = None
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1

def test_config_with_none_drexel_connect_base_url(config_args):
    config_args["drexel_connect_base_url"] = None
    config = Config(**config_args)
    result = config.validate()
    assert not result.ok
    assert len(result.errors) == 1