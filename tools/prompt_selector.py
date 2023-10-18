import re
import time
import openai
import pandas as pd
from typing import List, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from aexlutils import logger
from settings import SETTINGS
from custom_prompt_template import PromptSelectorTemplate
from utils import OpenAIQuery
import json
from pydantic import BaseModel, Field

class PromptSelectorInput(BaseModel):
    user_requirement: str = Field(description = "User required to query which pool and number of horses for ranking.")

class PromptSelectorTool(BaseTool):
    name = "Select prompt versions"
    description = """
        useful when you need to choose a correct prompt version based on certain pool for doing prediction and determine most profit return.
        You should understand user's requirement on betting and enter the requirement
        output will be one specific prompt version in string, available in all prompt choices.
        """
    args_schema: Type[BaseModel] = PromptSelectorInput

    def _run(self, user_requirement: str):
        response = get_all_prompt_version_from_json(user_requirement)
        return f"All available prompt version are {response}, you should choose one among them for user."

    def _arun(self, user_requirement: str):
        raise NotImplementedError("get_race_predicted_ranking does not support async")

# Helper function
def generate_full_prompt(user_requirement: str, prompt_gain_loss_table: list) -> str:
    prompt = PromptSelectorTemplate.create_prompt_template(
        user_requirement=user_requirement, 
        prompt_gain_loss_table=prompt_gain_loss_table
      )
    return prompt

def get_all_prompt_version_from_json(user_requirement: str) -> str:
    # Read gain loss json
    logger.info("Getting all prompt version from json for selection")
    prompt_gain_loss_table = []
    with open('./assets/prompt_gain_loss.json', 'r') as f:
        prompt_gain_loss_table = json.load(f)
    prompt = generate_full_prompt(user_requirement, prompt_gain_loss_table)
    response = OpenAIQuery.generate_response(prompt) 
    return response
