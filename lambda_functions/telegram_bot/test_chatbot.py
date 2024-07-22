from chatbot.event_handler import EventHandler
from aws_utils import get_record_from_dynamo

bot = EventHandler([])
answer = bot.run(
    "titolo: torneo di warhammer, descrizione: vieni a guerreggiare con noi!, data: 15 luglio, ora: 10-18, location: Qbo di Sommacampagna"
)
print(answer["output"])
