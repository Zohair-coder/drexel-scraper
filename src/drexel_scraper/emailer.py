# Make sure the following environment variables are set:
# AWS_DEFAULT_REGION
# AWS_ACCESS_KEY_ID
# AWS_SECRET_ACCESS_KEY

import boto3

from drexel_scraper import config


def send_email(subject: str, body: str) -> bool:
    topic_arn = config.topic_arn
    return publish_to_sns(topic_arn, subject, body)


def publish_to_sns(topic_arn: str | None, subject: str, body: str) -> bool:
    sns = boto3.client("sns", endpoint_url=config.sns_endpoint)

    if topic_arn is None:  # will be None for local testing
        topic_arn = get_sns_topic_arn("DrexelScheduler")

    response = sns.publish(TopicArn=topic_arn, Message=body, Subject=subject)
    if 200 <= response["ResponseMetadata"]["HTTPStatusCode"] < 300:
        return True
    return False


def get_sns_topic_arn(topic_name: str) -> str | None:
    sns = boto3.client("sns", endpoint_url=config.sns_endpoint)
    response = sns.list_topics()
    for topic in response["Topics"]:
        if topic_name in topic["TopicArn"]:
            assert isinstance(topic["TopicArn"], str), "TopicArn should be a string"
            return topic["TopicArn"]
    return None
