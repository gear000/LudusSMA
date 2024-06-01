from chatbot.event_handler import EventHandler

bot = EventHandler([])
answer = bot.run(
    "ciao, voglio creare un evento per il torneo di warhammer, il torneo dell'anno! sarà il 4 febbraio dalle 10 alle 18 alla sede di ludus di povegliano."
)
print(answer["output"])
