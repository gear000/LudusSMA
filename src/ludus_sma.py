from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAI
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_community.callbacks import get_openai_callback

from src.prompts import CREATE_IG_DECRIPTION, CREATE_DALLE_PROMPT


class LudusSMA:
    """
    Ludus BOT class.
    It creates description for social content, prompt for Dall-E and generates Dall-E image.
    """

    def __init__(
        self,
        description_template: str = CREATE_IG_DECRIPTION,
        dalle_template: str = CREATE_DALLE_PROMPT,
    ):
        """
        Create LudusSMA Bot object.

        Args:
            description_template (str): Prompt for the description generation.
            dalle_template (str): Prompt for the Dall-E prompt generation.
        """

        description_prompt = PromptTemplate.from_template(template=description_template)
        llm = OpenAI()
        output_parser = StrOutputParser()
        self.ig_description_generator = description_prompt | llm | output_parser

        dalle_prompt = PromptTemplate.from_template(template=dalle_template)
        self.dalle_prompt_generator = dalle_prompt | llm | output_parser

        self.dalle = DallEAPIWrapper()
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0

    def get_description(self, content_type: str, context: str) -> dict:
        """
        Function to answer the user question

        Args:
            content_type (str): The type of content the description is for: story | post.
            context (str): The context on which to generate the description.

        Returns:
            (dict): Contains bot answer and other metadata:
                description (str): The answer to the user's question
                prompt_token (int): Number of tokens in input.
                completion_token (int): Number of tokens generated.
                cost (int): Estimated cost.

        """

        with get_openai_callback() as cb:
            description = self.ig_description_generator.invoke(
                {"content_type": content_type, "context": context}
            )
            self.prompt_tokens += cb.prompt_tokens
            self.completion_tokens += cb.completion_tokens
            self.cost += cb.total_cost

        return {
            "description": description,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost": self.cost,
        }

    def get_dalle_image(self, context: str) -> dict:
        """
        Function to answer the user question

        Args:
            context (str): The context on which to generate the description.

        Returns:
            (dict): Contains bot answer and other metadata:
                description (str): The answer to the user's question
                prompt_token (int): Number of tokens in input.
                completion_token (int): Number of tokens generated.
                cost (int): Estimated cost.

        """

        with get_openai_callback() as cb:
            dalle_prompt = self.dalle_prompt_generator.invoke({"context": context})
            self.prompt_tokens += cb.prompt_tokens
            self.completion_tokens += cb.completion_tokens
            self.cost += cb.total_cost

        with get_openai_callback() as cb:
            dalle_img_url = self.dalle.run(dalle_prompt)
            self.prompt_tokens += cb.prompt_tokens
            self.completion_tokens += cb.completion_tokens
            self.cost += cb.total_cost

        return {
            "dalle_prompt": dalle_prompt,
            "dalle_image_url": dalle_img_url,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost": self.cost,
        }
