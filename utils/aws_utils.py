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


def put_s3_object(bucket_name: str, object_key: str, body: str):
    try:
        response = _S3_CLIENT.put_object(Bucket=bucket_name, Key=object_key, Body=body)
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


# region DynamoDB


def encode_record(record):
    converted_record = {}
    for key, value in record.items():
        if isinstance(value, str):
            converted_record[key] = {"S": value}
        elif isinstance(value, int) or isinstance(value, float):
            converted_record[key] = {"N": str(value)}
        elif isinstance(value, bool):
            converted_record[key] = {"BOOL": value}
        elif isinstance(value, list):
            converted_record[key] = {
                "L": [encode_record({"value": v})["value"] for v in value]
            }
        elif isinstance(value, dict):
            converted_record[key] = {"M": encode_record(value)}
        elif isinstance(value, set):
            if all(isinstance(v, str) for v in value):
                converted_record[key] = {"SS": list(value)}
            elif all(isinstance(v, int) or isinstance(v, float) for v in value):
                converted_record[key] = {"NS": list(map(str, value))}
            else:
                raise TypeError(f"Set non supportato con tipi misti: {type(value)}")
        else:
            raise TypeError(f"Tipo di dato non supportato: {type(value)}")
    return converted_record


def decode_record(record):
    converted_record = {}
    for key, value in record.items():
        if "S" in value:
            converted_record[key] = value["S"]
        elif "N" in value:
            converted_record[key] = (
                int(value["N"]) if value["N"].isdigit() else float(value["N"])
            )
        elif "BOOL" in value:
            converted_record[key] = value["BOOL"]
        elif "L" in value:
            converted_record[key] = [
                decode_record({"value": v})["value"] for v in value["L"]
            ]
        elif "M" in value:
            converted_record[key] = decode_record(value["M"])
        elif "SS" in value:
            converted_record[key] = set(value["SS"])
        elif "NS" in value:
            converted_record[key] = set(map(float, value["NS"]))
        else:
            raise TypeError(f"Tipo di dato non supportato: {type(value)}")
    return converted_record


def insert_record_in_dynamo(
    table_name: str,
    record: dict,
    dynamodb_client=boto3.client("dynamodb"),
):
    try:
        converted_record = encode_record(record)
        dynamodb_client.put_item(TableName=table_name, Item=converted_record)
        logger.info("Record saved successfully: ", record)
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in saving record: ", e)


def get_record_from_dynamo(
    table_name: str,
    key_name: str,
    key_value: str,
    dynamodb_client=boto3.client("dynamodb"),
):
    """
    Retrieves a record from a DynamoDB table based on the provided table name, key name, and key value.

    Args:
        table_name (str): The name of the DynamoDB table.
        key_name (str): The name of the key used to identify the record.
        key_value (str): The value of the key used to identify the record.
        dynamodb_client (boto3.client, optional): The DynamoDB client to use for the operation. Defaults to a client for the "eu-west-1" region.

    Returns:
        dict or None: The decoded record if found, or None if not found.
    """
    try:
        response = dynamodb_client.get_item(
            TableName=table_name, Key={key_name: {"S": key_value}}
        )
        print(response["Item"])
        return decode_record(response["Item"])
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in getting record: ", e)


def clear_history(
    table_name: str,
    user_id: str,
    dynamodb_client=boto3.client("dynamodb", region_name="eu-west-1"),
):
    """
    Clears the history for a specific user in a DynamoDB table.

    Args:
        table_name (str): The name of the DynamoDB table.
        user_id (str): The ID of the user whose history will be cleared.
        dynamodb_client (boto3.client, optional): The DynamoDB client to use for the operation. Defaults to a client for the "eu-west-1" region.
    """
    try:
        converted_record = encode_record({"user_id": user_id})
        dynamodb_client.put_item(TableName=table_name, Item=converted_record)
        print("History cleared successfully: ", user_id)
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("Error in clearing history: ", e)


# endregion

# region SQS


def send_message_in_sqs_queue(queue_name: str, message: dict):
    """
    Sends a message in a SQS queue.

    ### Args ###
        `queue_name` (str): The name of the SQS queue.
        `message` (dict): The message to send.
    """
    try:
        _SQS_CLIENT.send_message(QueueUrl=queue_name, MessageBody=message)
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


def create_scheduler(
    name_schudeler: str,
    schedule_expression: str,
    target_arn: str,
    role_arn: str,
    start_date: datetime,
    end_date: datetime,
    event: Event,
):
    try:
        _SCHEDULER_CLIENT.create_schedule(
            ActionAfterCompletion="DELETE",
            Name=name_schudeler,
            ScheduleExpression=schedule_expression,
            StartDate=start_date,
            EndDate=end_date,
            State="ENABLED",
            FlexibleTimeWindow={"MaximumWindowInMinutes": 10, "Mode": "FLEXIBLE"},
            Target={
                "Arn": target_arn,
                "RoleArn": role_arn,
                "Input": event.model_dump_json(exclude_none=True),
                "RetryPolicy": {
                    "MaximumRetryAttempts": 0,
                    "MaximumEventAgeInSeconds": 0,
                },
            },
        )
    except Exception as e:
        logger.error("Error in creating scheduler: ", e)
        raise e


# endregion
