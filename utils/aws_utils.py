import uuid
import boto3

from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from .logger_utils import *
from .models.model_utils import Event

# region AWS clients

_S3_CLIENT = boto3.client("s3")
_SSM_CLIENT = boto3.client("ssm")
_SQS_CLIENT = boto3.client("sqs")
_SCHEDULER_CLIENT = boto3.client("scheduler")

# endregion

# region SSM


def get_parameter(
    parameter_name: str,
    is_secure: bool = False,
) -> str | None:
    """
    Retrieve an encrypted parameter from AWS Systems Manager Parameter Store.

    :param parameter_name: string, the name of the parameter to retrieve
    :param is_secure: boolean, whether the parameter should be decrypted
    :param ssm_client: boto3 client, the client to use to retrieve the parameter
    :return: string or None, the value of the parameter if successful, None if not
    """

    try:
        # Get the parameter
        response = _SSM_CLIENT.get_parameter(
            Name=parameter_name, WithDecryption=is_secure
        )
        return response["Parameter"]["Value"]
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        return None


# endregion

# region S3


def get_s3_object(bucket_name: str, object_key: str):
    try:
        response = _S3_CLIENT.get_object(Bucket=bucket_name, Key=object_key)  # type: ignore  # noqa: E501
        return response["Body"]  # .read()#.decode("utf-8")
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        return None


def put_s3_object(bucket_name: str, object_key: str, body):
    try:
        response = _S3_CLIENT.put_object(Bucket=bucket_name, Key=object_key, Body=body)
        return response
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        return None


def delete_s3_object(bucket_name: str, object_key: str, recursive: bool = False):
    try:
        if recursive:
            objects = _S3_CLIENT.list_objects_v2(Bucket=bucket_name, Prefix=object_key)
            response = _S3_CLIENT.delete_objects(
                Bucket=bucket_name,
                Delete={
                    "Objects": [{"Key": obj["Key"]} for obj in objects["Contents"]]
                },
            )
        else:
            response = _S3_CLIENT.delete_object(Bucket=bucket_name, Key=object_key)

        return response
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        return None


def create_presigned_url(bucket_name, object_key, expiration=3600):
    try:
        response = _S3_CLIENT.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": object_key}
        )
        return response
    except ClientError as e:
        logger.error(e)
        return None


def list_s3_folders(bucket_name, prefix) -> list[str]:
    paginator = _S3_CLIENT.get_paginator("list_objects_v2")
    result = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter="/")

    folders = []
    for page in result:
        if "CommonPrefixes" in page:
            for common_prefix in page["CommonPrefixes"]:
                folders.append(common_prefix["Prefix"])

    return folders


# region SQS


def send_message_in_sqs_queue(
    queue_name: str,
    message: dict,
    message_deduplication_id: str = uuid.uuid4().hex,
    message_group_id: str = "default",
):
    """
    Sends a message in a SQS queue.

    ### Args ###
        `queue_name` (str): The name of the SQS queue.
        `message` (dict): The message to send.
    """
    try:
        _SQS_CLIENT.send_message(
            QueueUrl=queue_name,
            MessageBody=message,
            MessageDeduplicationId=message_deduplication_id,
            MessageGroupId=message_group_id,
        )
        logger.info("Message sent successfully")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in saving record: ", e)


def delete_message_from_sqs_queue(queue_name: str, receipt_handle: str):
    """
    Deletes a message from a SQS queue.

    ### Args ###
        `queue_name` (str): The name of the SQS queue.
        `receipt_handle` (str): The receipt handle of the message to delete.
    """
    try:
        _SQS_CLIENT.delete_message(QueueUrl=queue_name, ReceiptHandle=receipt_handle)
        logger.info("Message deleted successfully")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in saving record: ", e)


# endregion


# region Scheduler


def create_scheduler_group(scheduler_group_name: str, tags: list[dict]):
    try:
        _SCHEDULER_CLIENT.create_schedule_group(
            Name=scheduler_group_name,
            Tags=[{"Key": "projectID", "Value": "LudusSMA"}, *tags],
        )
    except Exception as e:
        logger.error("Error in creating scheduler group: ", e)
        raise e


def create_scheduler(
    name_schudeler: str,
    schedule_expression: str,
    target_arn: str,
    role_arn: str,
    start_date: datetime,
    end_date: datetime,
    event: Event,
    schedule_group_name: str = "default",
):
    try:
        _SCHEDULER_CLIENT.create_schedule(
            ActionAfterCompletion="DELETE",
            Name=name_schudeler,
            ScheduleExpression=schedule_expression,
            GroupName=schedule_group_name,
            StartDate=start_date,
            EndDate=end_date,
            State="ENABLED",
            FlexibleTimeWindow={"MaximumWindowInMinutes": 10, "Mode": "FLEXIBLE"},
            Target={
                "Arn": target_arn,
                "RoleArn": role_arn,
                "Input": event.model_dump_json(exclude_none=True),
            },
        )
    except Exception as e:
        logger.error("Error in creating scheduler: ", e)
        raise e


# endregion
