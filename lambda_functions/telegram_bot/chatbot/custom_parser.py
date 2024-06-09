import logging
from typing import Union
from langchain.agents.agent import AgentOutputParser

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers.json import parse_json_markdown

logger = logging.getLogger(__name__)


class CustomJSONAgentOutputParser(AgentOutputParser):
    """Parses tool invocations and final answers in JSON format.

    Expects output to be in one of two formats.

    If the output signals that an action should be taken,
    should be in the below format. This will result in an AgentAction
    being returned.

    ```
    {
      "action": "search",
      "action_input": "2+2"
    }
    ```

    If the output signals that a final answer should be given,
    should be in the below formats. This will result in an AgentFinish
    being returned.

    ```
    {
      "action": "Final Answer",
      "action_input": "4"
    }
    ```
    ```
    {
      "action": "Ask for info",
      "action_input": "Can you provide more info?"
    }
    ```
    """

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        try:
            response = parse_json_markdown(text)
            if isinstance(response, list):
                # gpt turbo frequently ignores the directive to emit a single action
                logger.warning("Got multiple action responses: %s", response)
                response = response[0]
            if response["action"] in ("Final Answer", "Ask for info"):
                return AgentFinish({"output": response["action_input"]}, text)
            else:
                return AgentAction(
                    response["action"], response.get("action_input", {}), text
                )
        except Exception as e:
            raise OutputParserException(f"Could not parse LLM output: {text}") from e

    @property
    def _type(self) -> str:
        return "json-agent"
