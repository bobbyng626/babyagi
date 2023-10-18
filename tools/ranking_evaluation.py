import re
import time
import openai
import pandas as pd
from typing import List, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from aexlutils import logger
from settings import SETTINGS
from custom_prompt_template import RankingEvaluationTemplate
from utils import OpenAIQuery
import json
from pydantic import BaseModel, Field

class RankingEvaluationInput(BaseModel):
    actual_ranking: list = Field(description="The actual ranking of a horse race")
    predicted_ranking: list = Field(description="The predicted ranking of a horse race generated")

class RankingEvaluationTool(BaseTool):
    name = "Evaluate predicted ranking"
    description = """
        useful when you need to evaluate the performance of the predicted ranking made by the prompt.
        It show possible winning and losing pattern of the predicted ranking comparing with the actual ranking
        You should enter the actual ranking of the race
        You should enter the predicted ranking of the race 
        output will be a JSON object to show which pool does the prediction hit, and which pool does not.
        """
    args_schema: Type[BaseModel] = RankingEvaluationInput

    def _run(self, actual_ranking: list, predicted_ranking: list):
        response = get_ranking_evaluation(actual_ranking, predicted_ranking)
        return response

    def _arun(self, actual_ranking: list, predicted_ranking: list):
        raise NotImplementedError("get_ranking_evaluation does not support async")

# Helper function
def generate_full_prompt(actual_ranking: list, predicted_ranking: list) -> str:
    prompt = RankingEvaluationTemplate.create_prompt_template(
        actual_ranking=actual_ranking,
        predicted_ranking=predicted_ranking
      )
    return prompt

def get_ranking_evaluation(actual_ranking: list, predicted_ranking: list) -> str:
    # Read gain loss json
    logger.info("Preparing evaluation")
    prompt = generate_full_prompt(actual_ranking, predicted_ranking)
    response = OpenAIQuery.generate_response(prompt) 
    return response
