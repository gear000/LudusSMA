from lambda_functions.utils.aws_utils import (
    insert_record_in_dynamo,
    insert_record_in_dynamo_awswr,
)
from datetime import datetime

st = datetime.now()
insert_record_in_dynamo(
    table_name="ChatsHistory",
    record={
        "user_id": "daniush",
        "chat_id": "dani_prova",
        "message_timestamp": str(datetime.now()),
        "chat_type": "event_creation",
    },
)
print(f"Tempo esecuzione boto3: {datetime.now() - st}")

st = datetime.now()
insert_record_in_dynamo_awswr(
    table_name="ChatsHistory",
    record=[
        {
            "user_id": "heinush",
            "chat_id": "heinush_prova",
            "message_timestamp": str(datetime.now()),
            "chat_type": "event_creation",
        },
    ],
)
print(f"Tempo esecuzione awswr: {datetime.now() - st}")
