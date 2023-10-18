import re
import time
import openai
import pandas as pd
from typing import List, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from aexlutils import logger
from settings import SETTINGS
# from custom_prompt_template import AnalyzeInsightTemplate
from utils import OpenAIQuery
import json
from pydantic import BaseModel, Field

class AnalyzeInsightInput(BaseModel):
    race_data: str = Field(description="All the data of a horse race from the user")

class AnalyzeInsightTool(BaseTool):
    name = "Analyze a horse race winning group"
    description = """
        useful when you need to analyze one horse race data with some intelligent insight, by finding the winning group of the race.
        enter user passed current race data to get the winning group of the race.
        output will be a a group that has higher chance to win the race.
        """
    args_schema: Type[BaseModel] = AnalyzeInsightInput

    def _run(self):
        response = analyze_insight()
        return response

    def _arun(self):
        raise NotImplementedError("analyze_insight does not support async")

# # Helper function
# def generate_full_prompt(actual_ranking: list, predicted_ranking: list) -> str:
#     prompt = AnalyzeInsightTemplate.create_prompt_template(
#         actual_ranking=actual_ranking,
#         predicted_ranking=predicted_ranking
#       )
#     return prompt

def analyze_insight(race_data: str) -> str:
    # Read gain loss json
    logger.info("Preparing analyze_insight")
    # prompt = generate_full_prompt(actual_ranking, predicted_ranking)
    # prompt = ""
    # response = OpenAIQuery.generate_response(prompt)
    response = "The data analyzed the horse race successfully, it showed that win odds group '2' horse have more chance to win the race, its ranking should be ranked front."
    return response
