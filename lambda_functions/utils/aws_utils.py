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


# =====================
# DYNAMO


def convert_record(record):
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
                "L": [convert_record({"value": v})["value"] for v in value]
            }
        elif isinstance(value, dict):
            converted_record[key] = {"M": convert_record(value)}
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


def insert_record_in_dynamo(
    table_name: str,
    record: dict,
    dynamodb_client=boto3.client("dynamodb", region_name="eu-west-1"),
):
    try:
        converted_record = convert_record(record)
        dynamodb_client.put_item(TableName=table_name, Item=converted_record)
        logger.info("Record saved successfully: ", record)
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in saving record: ", e)


def get_record_from_dynamo(
    table_name: str,
    key_name: str,
    key_value: str,
    dynamodb_client=boto3.client("dynamodb", region_name="eu-west-1"),
):
    try:
        response = dynamodb_client.get_item(
            TableName=table_name, Key={key_name: {"S": key_value}}
        )
        return response["Item"]
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in getting record: ", e)


# OLD
# def insert_record_in_dynamo_awswr(
#     table_name: str,
#     record: list,
#     # dynamodb_client=boto3.client("dynamodb", region_name="eu-west-1"),
# ):
#     try:
#         wr.dynamodb.put_items(items=record, table_name=table_name)
#         print("Record saved successfully: ", record)
#     except (NoCredentialsError, PartialCredentialsError) as e:
#         print("Error in saving record: ", e)

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
