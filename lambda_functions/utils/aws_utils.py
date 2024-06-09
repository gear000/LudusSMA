from datetime import datetime
import json
import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

### Logger ###
logger = logging.getLogger("AWS Utils Logger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)


def get_parameter(
    parameter_name: str,
    is_secure: bool = False,
    ssm_client=boto3.client("ssm"),
    logger=logger,
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
        response = ssm_client.get_parameter(
            Name=parameter_name, WithDecryption=is_secure
        )
        return response["Parameter"]["Value"]
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        return None


### Dynamo ###


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


### SQS QUEUES ###


def send_message_in_sqs_queue(
    queue_name: str,
    message: dict,
    sqs_client=boto3.client("sqs"),
    logger=logger,
):
    try:
        sqs_client.send_message(QueueUrl=queue_name, MessageBody=message)
        logger.info("Message sent successfully")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in saving record: ", e)


def delete_message_from_sqs_queue(
    queue_name: str,
    receipt_handle: str,
    sqs_client=boto3.client("sqs"),
    logger=logger,
):
    try:
        sqs_client.delete_message(QueueUrl=queue_name, ReceiptHandle=receipt_handle)
        logger.info("Message deleted successfully")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in saving record: ", e)


### EventBridge Scheduler ###


def create_scheduler(
    name_schudeler: str,
    schedule_expression: str,
    target_arn: str,
    role_arn: str,
    input: dict,
    start_date: datetime,
    end_date: datetime,
    scheduler_client=boto3.client("scheduler"),
):
    try:
        scheduler_client.create_schedule(
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
                "Input": json.dumps(input),
            },
        )
    except Exception as e:
        logger.error("Error in creating scheduler: ", e)
        raise e