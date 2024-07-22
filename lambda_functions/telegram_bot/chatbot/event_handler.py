from langchain_aws import ChatBedrock

from langchain.prompts.prompt import PromptTemplate

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.tools import StructuredTool
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_community.chat_message_histories import (
    DynamoDBChatMessageHistory,
)

from langchain.agents.format_scratchpad import format_log_to_messages
from langchain.agents.json_chat.prompt import TEMPLATE_TOOL_RESPONSE
from langchain.agents import tool
from langchain.agents import AgentExecutor
from langchain.tools.render import render_text_description

import logging
import json
import os
from datetime import date, datetime

from .prompts import EVENT_SYSTEM_PROMPT, EVENT_TOOLS_PROMPT, CHECK_INFO_PROMPT
from .custom_parser import CustomJSONAgentOutputParser
from .tools import create_schedulers
from utils.aws_utils import list_s3_folders


S3_BUCKET_IMAGES_NAME = os.getenv("S3_BUCKET_IMAGES_NAME", "")
DYNAMODB_TABLE_CHATS_HISTORY_NAME = os.getenv("DYNAMODB_TABLE_CHATS_HISTORY_NAME", "")

logger = logging.getLogger(__name__)


def create_agent(prompt: str, tools: list):
    """
    Creates agent with given prompt and tools, using CustomJSONAgentOutputParser
    """
    return (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_log_to_messages(
                x["intermediate_steps"], template_tool_response=TEMPLATE_TOOL_RESPONSE
            ),
            history=lambda session_id: DynamoDBChatMessageHistory(
                table_name=DYNAMODB_TABLE_CHATS_HISTORY_NAME,
                session_id=session_id,
                primary_key_name="user_id",
            ),
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
        user_id: str,
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

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0

    def _define_tools(self) -> list:
        event_types = [
            elem.strip("/").split("/")[-1]
            for elem in list_s3_folders(S3_BUCKET_IMAGES_NAME, "clean-images/")
        ] + "other"

        def create_event(specifics: str):
            """Creates the event."""

            spec_dict: dict = json.loads(specifics)

            other_info = spec_dict.get("other_info")
            if other_info is None or len(other_info) < 3:
                spec_dict["other_info"] = None

            event_date = spec_dict.get("date", "")
            if len(event_date) == 10:
                event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
                if event_date < date.today():
                    event_date = date(
                        event_date.year + 1, event_date.month, event_date.day
                    )
            else:
                event_date = None
            spec_dict["date"] = event_date.strftime("%Y-%m-%d")

            spec_dict["title"] = spec_dict["title"].title()
            print(spec_dict)

            if spec_dict["event_type"] == "other":
                return "Failed to create the event: no existing image for selected event type. Please ask the user to upload the image first."

            check_info_chain = (
                PromptTemplate.from_template(CHECK_INFO_PROMPT)
                | ChatBedrock(
                    model_id="mistral.mixtral-8x7b-instruct-v0:1",
                    region_name="us-east-1",
                    streaming=False,
                )
                | StrOutputParser()
            )
            missing = check_info_chain.invoke(
                {"input": json.dumps(spec_dict), "event_types": event_types}
            )
            if "OK" in missing:
                event_date = datetime(event_date.year, event_date.month, event_date.day)
                print(f"Create event with: {specifics}")
                create_schedulers(spec_dict, event_date)
                return "Event created"
            else:
                return (
                    "Failed to create the event:"
                    + missing
                    + "\nPlease ask the user the missing information."
                )

        description = f"""
            Creates the event. Syntax:
            {{
                "title"
                "description"
                "date" // must be of the format YYYY-MM-DD
                "time" // as the user input
                "event_type" // must be one of {event_types}
                "location"
                "other_info" // optional
            }}"""

        event_tool = StructuredTool.from_function(
            func=create_event,
            name="create_event",
            description=description,
        )

        @tool
        def ask_for_info(message: str):
            """
            Ask the user for additional info. Syntax: Message to the user in ITALIAN.
            """
            pass

        return [event_tool, ask_for_info]

    def run(self, message: str, user_id: str):

        result = self.agent_executor.invoke(
            {
                "input": message,
                "today": date.today().strftime("%d/%m/%Y"),
            },
            config={"configurable": {"session_id": user_id}},
        )

        history = DynamoDBChatMessageHistory(
            table_name=DYNAMODB_TABLE_CHATS_HISTORY_NAME,
            session_id=user_id,
            primary_key_name="user_id",
        )
        history.add_user_message(message)
        history.add_ai_message(result["output"])
