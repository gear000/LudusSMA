import langchain
from chatbot.event_handler import EventHandler

langchain.debug = True

bot = EventHandler([])
answer = bot.run(
    "Come mi chiamo?",
    user_id="0987",
)
print(answer["output"])
