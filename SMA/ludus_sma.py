from langchain.prompts.prompt import PromptTemplate
from langchain.docstore.document import Document
from langchain_community.callbacks import get_openai_callback
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAI

from prompts import CREATE_IG_DECRIPTION


class LudusSMA:
    """
    Base BOT class.
    It handles the search part and the formulation of the answer.

    To be extended depending on the use case.
    """

    def __init__(
        self,
        openai_key: str,
        generate_template: str = CREATE_IG_DECRIPTION,
    ):
        """
        Create Base Bot object.

        Args:
            openai_key (str): Contains key for OpenAI service.
            generate_template (str): Prompt for the generation.
        """

        prompt = PromptTemplate.from_template(template=generate_template)
        llm = OpenAI(api_key=openai_key)
        output_parser = StrOutputParser()
        self.generate = prompt | llm | output_parser

        self.knowledge: str = None

        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0

    def answer(self, message: str = "") -> dict:
        """
        Function to answer the user question

        Args:
            message (str): The user input

        Returns:
            (dict): Contains bot answer and other metadata:
                answer (str): The answer to the user's question
                prompt_token (int): Number of tokens in input.
                completion_token (int): Number of tokens generated.
                cost (int): Estimated cost.

        """

        with get_openai_callback() as cb:
            answer = self.generate.invoke(
                {"knowledge": self.knowledge, "user_question": message}
            )
            self.prompt_tokens += cb.prompt_tokens
            self.completion_tokens += cb.completion_tokens
            self.cost += cb.total_cost

        return {
            "answer": answer,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost": self.cost,
        }

    def run(self, message: str):
        """
        Main function. Handles search part and answer formulation.

        Args:
            message (str): The user message.

        Returns:
            (dict): Contains bot answer and other metadata:
                answer (str): The answer to the user's question
                prompt_token (int): Number of tokens in input.
                completion_token (int): Number of tokens generated.
                cost (int): Estimated cost.
        """

        # -------------------------------- ANSWER
        return self.answer(message)
