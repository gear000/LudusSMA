from lambda_functions.utils.aws_utils import (
    insert_record_in_dynamo,
    get_record_from_dynamo,
)
from datetime import datetime

# st = datetime.now()
# insert_record_in_dynamo(
#     table_name="ChatsHistory",
#     record={
#         "user_id": "daniush",
#         "chat_id": "dani_prova",
#         "message_timestamp": str(datetime.now()),
#         "chat_type": "event_creation",
#     },
# )
# print(f"Tempo esecuzione boto3: {datetime.now() - st}")

print(
    get_record_from_dynamo(
        table_name="ChatsHistory", key_name="user_id", key_value="daniush"
    )
)
