import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError


def get_parameter(
    parameter_name: str, is_secure: bool = False, ssm_client=boto3.client("ssm")
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
        print(f"An error occurred: {e}")
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
        print("Record saved successfully: ", record)
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("Error in saving record: ", e)
