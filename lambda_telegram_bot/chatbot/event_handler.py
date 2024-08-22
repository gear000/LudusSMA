from operator import itemgetter
from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableLambda

from utils.models.model_utils import OutputCreateEvent
from utils.logger_utils import *
from .prompts import (
    LLAMA_31_CHECK_INFO_PROMPT,
    CHECK_INFO_USER_PROMPT,
    CHECK_INFO_ASSISTANT_PROMPT,
)


def _prepare_input(msg_list: list):
    input_text = ""
    for elem in msg_list:
        if elem[0] == "user":
            input_text += CHECK_INFO_USER_PROMPT.format(user_message=elem[1])
        elif elem[0] == "assistant":
            input_text += CHECK_INFO_ASSISTANT_PROMPT.format(assistant_message=elem[1])
    return input_text


output_parser = PydanticOutputParser(
    pydantic_object=OutputCreateEvent,
)

check_info_chain = (
    {
        "input_messages": itemgetter("input") | RunnableLambda(_prepare_input),
        "today": itemgetter("today"),
    }
    | PromptTemplate.from_template(
        LLAMA_31_CHECK_INFO_PROMPT,
        partial_variables={
            "formatting_guidelines": output_parser.get_format_instructions()
        },
    )
    | ChatBedrockConverse(
        model="meta.llama3-1-70b-instruct-v1:0",
        region_name="us-west-2",
    )
    | output_parser
)
