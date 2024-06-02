from chatbot.event_handler import EventHandler
from aws_utils import get_record_from_dynamo

record = get_record_from_dynamo(
    table_name="ChatsHistory", key_name="user_id", key_value="505969510"
)
chat_history = record.get("messages", [])

bot = EventHandler([])
answer = bot.run(
    "titolo: torneo di warhammer, descrizione: vieni a guerreggiare con noi!, data: 15 marzo, ora: 10-18, location: Qbo di Sommacampagna"
)
print(answer["output"])
