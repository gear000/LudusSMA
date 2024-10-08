import os
import uuid
import boto3
import time
import requests

from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from .logger_utils import *
from .models.model_utils import Event

# region AWS clients

_S3_CLIENT = boto3.client("s3")
_SSM_CLIENT = boto3.client("ssm")
_SQS_CLIENT = boto3.client("sqs")
_SCHEDULER_CLIENT = boto3.client("scheduler")
_TRANSCRIBE_CLIENT = boto3.client("transcribe")

# endregion

# region Defaults

TRANSCRIBE_CUSTOM_VOCABULARY_NAME = os.getenv("TRANSCRIBE_CUSTOM_VOCABULARY_NAME")

# endregion

# region SSM


def get_parameter(
    parameter_name: str,
    is_secure: bool = False,
) -> str:
    """
    Retrieve an encrypted parameter from AWS Systems Manager Parameter Store.

    :param parameter_name: string, the name of the parameter to retrieve
    :param is_secure: boolean, whether the parameter should be decrypted
    :param ssm_client: boto3 client, the client to use to retrieve the parameter
    :return: string, the value of the parameter if successful
    """

    try:
        # Get the parameter
        response = _SSM_CLIENT.get_parameter(
            Name=parameter_name, WithDecryption=is_secure
        )
        return response["Parameter"]["Value"]
    except ClientError as e:
        logger.error(f"Failed to get parameter: {e}")
        raise e


def set_parameter(parameter_name: str, parameter_value: str, parameter_type: str):
    """
    Set an encrypted parameter in AWS Systems Manager Parameter Store.

    :param parameter_name: string, the name of the parameter to set
    :param parameter_value: string, the value of the parameter to set
    :param parameter_type: string, the type of the parameter to set
    :param ssm_client: boto3 client, the client to use to set the parameter
    :return: None
    """
    try:
        response = _SSM_CLIENT.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type=parameter_type,
            Overwrite=True,
        )
        return response
    except ClientError as e:
        logger.error(f"Failed to set new parameter: {e}")
        raise e


# endregion

# region S3


def get_s3_object(bucket_name: str, object_key: str):
    try:
        response = _S3_CLIENT.get_object(Bucket=bucket_name, Key=object_key)  # type: ignore  # noqa: E501
        return response["Body"]  # .read()#.decode("utf-8")
    except ClientError as e:
        logger.error(f"An error occurred: {e}")
        return None


def list_s3_objects(bucket_name: str, prefix: str) -> list[str]:
    try:
        response = _S3_CLIENT.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        return response["Contents"]
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


def move_s3_object(bucket_name: str, object_key: str, new_key: str):
    try:
        response = _S3_CLIENT.copy_object(
            Bucket=bucket_name, Key=new_key, CopySource=f"{bucket_name}/{object_key}"
        )
        delete_s3_object(bucket_name=bucket_name, object_key=object_key)
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


def create_schedule_group(schedule_group_name: str, tags: list[dict]):
    try:
        _SCHEDULER_CLIENT.create_schedule_group(
            Name=schedule_group_name,
            Tags=[{"Key": "projectID", "Value": "LudusSMA"}, *tags],
        )
    except Exception as e:
        logger.error("Error in creating schedule group: ", e)
        raise e


def delete_schedule_group(schedule_group_name: str):
    try:
        _SCHEDULER_CLIENT.delete_schedule_group(Name=schedule_group_name)
    except Exception as e:
        logger.error("Error in deleting schedule group: ", e)
        raise e


def create_schedule(
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
        logger.error("Error in creating schedule: ", e)
        raise e


def list_schedule_groups(exclude_default: bool = False) -> list[dict[str, str]]:
    """
    Lists all schedule groups, excluding the ones that are DELETING or DEFAULT
    if exclude_default is True.

    Returns:
        A list of dictionaries, each containing the details of a schedule group.
    """
    schedule_groups = _SCHEDULER_CLIENT.list_schedule_groups()["ScheduleGroups"]
    return [
        sg
        for sg in schedule_groups
        if sg["State"] != "DELETING"
        and (not exclude_default or sg["Name"] != "default")
    ]

def delete_schedule_groups(schedule_name: str):
    all_groups_response = _SCHEDULER_CLIENT.list_schedule_groups()
    all_schedules_response = _SCHEDULER_CLIENT.list_schedules()
    schedule_groups_all = [] # Lista di tutti gli schedule groups esistenti
    for group in all_groups_response['ScheduleGroups']:
        schedule_groups_all.append(group['Name'])
        schedule_groups_all = set(schedule_groups_all)
    schedule_groups_full = [] # Lista di schedule groups che hanno schedules al loro interno
    for schedule in all_schedules_response['Schedules']:
        schedule_groups_full.append(schedule['GroupName'])
        schedule_groups_full = set(schedule_groups_full)
    schedule_groups_empty = schedule_groups_all - schedule_groups_full
    for group_to_delete in schedule_groups_empty:
        if group_to_delete != "default":
            delete_schedule_group(schedule_group_name=group_to_delete)

def list_tags(resource_arn: str):
    try:
        response = _SCHEDULER_CLIENT.list_tags_for_resource(ResourceArn=resource_arn)
        return response["Tags"]
    except Exception as e:
        logger.error("Error in listing tags: ", e)
        raise e


# endregion

# region Transcribe


def transcribe_audio(audio_key: str) -> str:

    transcription_job_name = uuid.uuid4().hex
    _TRANSCRIBE_CLIENT.start_transcription_job(
        TranscriptionJobName=transcription_job_name,
        Media={"MediaFileUri": audio_key},
        MediaFormat="mp3",
        LanguageCode="it-IT",
        Settings={
            "VocabularyName": TRANSCRIBE_CUSTOM_VOCABULARY_NAME,
        },
    )

    # Attendere che la trascrizione sia completata
    while True:
        status = _TRANSCRIBE_CLIENT.get_transcription_job(
            TranscriptionJobName=transcription_job_name
        )
        if status["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
            break
        elif status["TranscriptionJob"]["TranscriptionJobStatus"] == "FAILED":
            raise Exception("Transcription failed.")

        time.sleep(0.5)

    transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    transcript = requests.get(transcript_uri).json()

    return transcript["results"]["transcripts"][0]["transcript"]


# endregion
