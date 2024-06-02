from langchain_aws import ChatBedrock

from langchain.prompts.prompt import PromptTemplate

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.agents.json_chat.prompt import TEMPLATE_TOOL_RESPONSE
from langchain.agents import tool
from langchain.agents import AgentExecutor
from langchain.tools.render import render_text_description

import logging
import json
from datetime import date

from .prompts import EVENT_SYSTEM_PROMPT, EVENT_TOOLS_PROMPT, CHECK_INFO_PROMPT
from .custom_parser import CustomJSONAgentOutputParser


logger = logging.getLogger(__name__)


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


def create_agent(prompt: str, tools: list):
    """
    Creates agent with given prompt and tools, using CustomJSONAgentOutputParser
    """
    return (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_log_to_messages(
                x["intermediate_steps"], template_tool_response=TEMPLATE_TOOL_RESPONSE
            )
        )
        | prompt.partial(
            tools=render_text_description(list(tools)),
            tool_names=", ".join([t.name for t in tools]),
        )
        | ChatBedrock(
            model_id="mistral.mixtral-8x7b-instruct-v0:1",
            region_name="us-east-1",
            streaming=False,
        )
        | CustomJSONAgentOutputParser()
    )


def create_agent_executor(prompt: str, tools: list):
    """
    Creates agent with given prompt and tools
    """
    agent_executor = AgentExecutor(
        agent=create_agent(prompt, tools),
        tools=tools,
        return_intermediate_steps=True,
        verbose=True,
        max_iterations=5,
    )
    agent_executor.agent.stream_runnable = False
    return agent_executor


class EventHandler:
    """
    Ludus BOT class.
    It handles the creation of events.
    """

    def __init__(
        self,
        chat_history: list = [],
    ):
        """
        Create EventHandler Bot object.

        Args:
            chat_history (list): Chat history:
            [
                {
                    "content":"content",
                    "author":"bot"|"user",
                    "timestamp":str(datetime.now())
                }
            ]
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

        self.agent_executor = create_agent_executor(prompt, tools)

        self.chat_history = history_to_list(chat_history)

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0

    def _define_tools(self) -> list:

        @tool
        def create_event(specifics: str):
            """
            Creates the event. Syntax:
            {
                "title"
                "description"
                "date" // must be of the format DD/MM/YYYY
                "time" // as the user input
                "location"
                "other_info" // optional
            }
            """

            spec_dict: dict = json.loads(specifics)

            other_info = spec_dict.get("other_info")
            if other_info is None or len(other_info) < 3:
                spec_dict["other_info"] = None

            event_date = spec_dict.get("date")
            if event_date is not None and event_date[-4:] < str(date.today().year):
                spec_dict["date"] = None

            spec_dict["title"] = spec_dict["title"].title()
            print(spec_dict)

            check_info_chain = (
                PromptTemplate.from_template(CHECK_INFO_PROMPT)
                | ChatBedrock(
                    model_id="mistral.mixtral-8x7b-instruct-v0:1",
                    region_name="us-east-1",
                    streaming=False,
                )
                | StrOutputParser()
            )
            missing = check_info_chain.invoke({"input": json.dumps(spec_dict)})
            if missing.strip() == "OK":
                print(f"Create event with: {specifics}")
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
