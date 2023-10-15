import boto3
import config

def send_email(subject: str, body: str) -> bool:
    topic_arn = config.topic_arn
    return publish_to_sns(topic_arn, subject, body)

def publish_to_sns(topic_arn: str, subject: str, body: str) -> bool:
    sns = boto3.client("sns")
    response = sns.publish(TopicArn=topic_arn, Message=body, Subject=subject)
    if  200 <= response["ResponseMetadata"]["HTTPStatusCode"] < 300:
        return True
    return False