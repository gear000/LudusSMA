from langchain_aws import ChatBedrock
from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain.agents import AgentExecutor, create_json_chat_agent


from .prompts import EVENT_SYSTEM_PROMPT, EVENT_TOOLS_PROMPT, CHECK_INFO_PROMPT


def history_to_str(chat: list) -> str:
    """
    chat = [
        {
            "content":"content",
            "author":"bot"|"user",
            "timestamp":str(datetime.now())
        }
    ]

    Returns:
        history (str)
    """
    chat = sorted(chat, lambda x: x["timestamp"])
    history = ""
    for msg in chat:
        if msg["author"] == "user":
            history += "[INST]" + msg["content"] + "[\INST]"
        elif msg["author"] == "bot":
            history += msg["content"]

    return history


def history_to_list(chat_history: list) -> list[BaseMessage]:
    """
    chat = [
        {
            "content":"content",
            "author":"bot"|"user",
            "timestamp":str(datetime.now())
        }
    ]

    Returns:
        history (list)
    """
    chat_history.sort(key=lambda x: x["timestamp"])
    history = []
    for msg in chat_history:
        if msg["author"] == "user":
            history.append(AIMessage(content=msg["content"]))
        elif msg["author"] == "bot":
            history.append(HumanMessage(content=msg["content"]))

    return history


class EventHandler:
    """
    Ludus BOT class.
    It creates description for social content, prompt for Dall-E and generates Dall-E image.
    """

    def __init__(
        self,
        chat_history: list = [],
    ):
        """
        Create EventHandler Bot object.

        Args:
            event_template (str): Prompt for the event generation.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", EVENT_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", EVENT_TOOLS_PROMPT),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

        tools = self._define_tools()

        self.agent_executor = AgentExecutor(
            agent=create_json_chat_agent(
                ChatBedrock(
                    model_id="mistral.mixtral-8x7b-instruct-v0:1",
                    region_name="us-east-1",
                ),
                tools,
                prompt,
                stop_sequence=False,
            ),
            tools=tools,
            return_intermediate_steps=True,
            verbose=True,
        )

        self.chat_history = history_to_list(chat_history)

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0

    def _define_tools(self) -> list:

        @tool
        def create_event(specifics: str):
            """Creates the event. Syntax: event name; event description; date; start time; ending time; adress."""
            splitted = specifics.split(";")
            check_info_chain = (
                PromptTemplate.from_template(CHECK_INFO_PROMPT)
                | ChatBedrock(
                    model_id="mistral.mixtral-8x7b-instruct-v0:1",
                    region_name="us-east-1",
                )
                | StrOutputParser()
            )
            missing = check_info_chain.invoke({"input": specifics})
            if missing.strip() == "OK":
                print(f"Create event with: {splitted}")
                return "Event created"
            else:
                return (
                    "Failed to create the event:"
                    + missing
                    + "\nPlease ask the user the missing information."
                )

        return [create_event]

    def run(self, message: str):
        return self.agent_executor.invoke(
            {"input": message, "chat_history": self.chat_history}
        )
