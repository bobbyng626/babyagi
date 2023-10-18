import re
import time
import openai
import pandas as pd
from aexlutils import logger
from typing import List, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from custom_prompt_template import RankingFilterTemplate
from utils import OpenAIQuery

from settings import SETTINGS
from pydantic import BaseModel, Field

class RankingFilterInput(BaseModel):
    user_requirement: str = Field()
    predicted_ranking_full: list = Field(description = "A list of predicted rankings")

class RankingFilterTool(BaseTool):
    name = "Output final ranking to user"
    description = """
        useful when you need return the final ranking to user, after you have the predicted ranking already.
        You should enter the predicted ranking list and user requirement. 
        output will be a final ranking for user to bet, according to user's requirement on how many horses to predict.
        """
    args_schema: Type[BaseModel] = RankingFilterInput
    return_direct: bool = True
    def _run(self, user_requirement: str, predicted_ranking_full: list):
        response = get_ranking_filter(user_requirement, predicted_ranking_full)
        return response

    def _arun(self, user_requirement: str):
        raise NotImplementedError("get_ranking_filter does not support async")

# Helper function
def generate_full_prompt(user_requirement: str, predicted_ranking_full: list) -> str:
    prompt = RankingFilterTemplate.create_prompt_template(
        user_requirement=user_requirement, 
        predicted_ranking_full=predicted_ranking_full
      )
    return prompt

def get_ranking_filter(user_requirement: str, predicted_ranking_full: str) -> str:
    logger.info("Filtering ranking")
    prompt = generate_full_prompt(user_requirement, predicted_ranking_full)
    response = OpenAIQuery.generate_response(prompt)
    print()
    return f'The final ranking according to your betting requirement is {response}.'