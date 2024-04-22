from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAI
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai.chat_models import ChatOpenAI

from langchain_community.llms import Bedrock


from prompts import EVENT_PROMPT
from operator import itemgetter


def history_to_str(chat: list) -> str:
    """
    chat = [
        {
            "text":"text",
            "author":"bot"|"user",
            "timestamp":str(datetime.now())
        }
    ]

    Returns:
        hostory (str)
    """
    chat = sorted(chat, lambda x: x["timestamp"])
    history = ""
    for msg in chat:
        if msg["author"] == "user":
            history += "[INST]" + msg["text"] + "[\INST]"
        elif msg["author"] == "bot":
            history += msg["text"]

    return history


class EventHandler:
    """
    Ludus BOT class.
    It creates description for social content, prompt for Dall-E and generates Dall-E image.
    """

    def __init__(
        self,
        chat: list = [],
        event_template: str = EVENT_PROMPT,
    ):
        """
        Create EventHandler Bot object.

        Args:
            event_template (str): Prompt for the event generation.
        """

        event_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", event_template),
                ("human", "[INST]{input}[\INST]"),
            ]
        )
        # llm = ChatOpenAI()
        llm = Bedrock(
            credentials_profile_name="bedrock-admin", model_id="meta.llama2-70b-chat-v1"
        )
        output_parser = StrOutputParser()
        self.event_handler = (
            {
                "knowledge": itemgetter("knowledge"),
                "chat_history": itemgetter("chat_history"),
                "input": itemgetter("input"),
            }
            | event_prompt
            | llm
            | output_parser
        )

        self.chat = chat

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0

    def run(self, message: str):
        self.event_handler.invoke(
            {"input": message, "chat_history": history_to_str(self.chat)}
        )
