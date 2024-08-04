from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate

from langchain.agents import tool

from typing import TypedDict, Annotated, List, Union
from langchain_core.agents import AgentAction, AgentFinish
import operator

import logging
from datetime import datetime

from .prompts import CHECK_INFO_PROMPT
from .tools import create_schedulers

# from utils.models.model_utils import output_parser

# region UTILS

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from langchain_core.output_parsers import JsonOutputParser


class Event(BaseModel):
    title: str = Field(description="Title of the event")
    description: str = Field(description="Description of the event")
    start_date: datetime = Field(
        description="Start date of the event. Must be in the format %Y-%m-%dT%H:%M:%S"
    )
    end_date: datetime = Field(
        description="End date of the event. Must be in the format %Y-%m-%dT%H:%M:%S"
    )
    location: str = Field(description="Location of the event")
    other_info: Optional[str] = Field(description="Other information about the event")
    event_type: Optional[str] = Field(description="Event type")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def convert_str2datetime(cls, v: str, info: ValidationInfo):
        try:
            return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
        except:
            raise ValueError(
                f"{info.field_name} must be a string in the format %Y-%m-%dT%H:%M:%S"
            )


class OutputCreateEvent(BaseModel):
    clarification: Optional[str] = Field(description="Question to ask the user")
    event: Optional[Event] = Field(description="The event to be created")


output_parser = JsonOutputParser(pydantic_object=OutputCreateEvent)


# endregion


logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    input: str
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]


check_info_chain = (
    ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                CHECK_INFO_PROMPT,
                partial_variables={
                    "formatting_guidelines": output_parser.get_format_instructions()
                },
            ),
            ("human", "Ecco il mio report:\n{input}"),
        ]
    )
    | ChatBedrockConverse(
        model="meta.llama3-70b-instruct-v1:0",
        region_name="us-east-1",
    )
    | output_parser
)
