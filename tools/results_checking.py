import re
import time
import openai
import pandas as pd
from typing import List, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from aexlutils import logger
from settings import SETTINGS
# from custom_prompt_template import PastRecordFetcherTemplate
from utils import OpenAIQuery
import json
from pydantic import BaseModel, Field

from custom_prompt_template import RankingEvaluationTemplate

class ResultsCheckingInput(BaseModel):
    initial_objective: str = Field(description="Initial objective from user input")
    accumulated_observation: str = Field(description="Accumulated observation from agent past answers")

class ResultsCheckingTool(BaseTool):
    name = "Check answer tool"
    description = """
        useful everytime you observed some outcome from other tools, when you need to check you can return the answer to user already or not.
        It is useful to check the requirement process, do not loop this tool when you get outcome from this tool.
        It acts as a final answering steps to user, use this tool every time you obtained some answer and observation, to check you fulfilled user requirement or not.
        """
    args_schema: Type[BaseModel] = ResultsCheckingInput

    def _run(self, initial_objective: str, accumulated_observation: str):
        response = get_results_checking(initial_objective, accumulated_observation)
        return response

    def _arun(self, prompt: str):
        raise NotImplementedError("get_results_checking does not support async")

# Helper function
def generate_full_prompt(initial_objective: str, accumulated_observation: str) -> str:
    prompt = RankingEvaluationTemplate.create_prompt_template(
        initial_objective=initial_objective,
        accumulated_observation=accumulated_observation
      )
    return prompt

def get_results_checking(initial_objective: str, accumulated_observation: str) -> str:
    # Read gain loss json
    logger.info("Preparing result checking")
    prompt = generate_full_prompt(initial_objective, accumulated_observation)
    response = OpenAIQuery.generate_response(prompt) 
    return response

