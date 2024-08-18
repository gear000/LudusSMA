from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.chat import SystemMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from utils.models.model_utils import OutputCreateEvent
from utils.logger_utils import *
from .prompts import CHECK_INFO_PROMPT


output_parser = PydanticOutputParser(
    pydantic_object=OutputCreateEvent,
)

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
        model="meta.llama3-1-405b-instruct-v1:0",
        region_name="us-west-2",
    )
    | output_parser
)
