from chatbot.event_handler import EventHandler

bot = EventHandler([])
answer = bot.run(
    "titolo: torneo di warhammer, descrizione: vieni a guerreggiare con noi!, data: 15 luglio, ora: 10-18, location: Qbo di Sommacampagna"
)
print(answer["output"])
