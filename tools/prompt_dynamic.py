import re
import time
import openai
import pandas as pd
from typing import List, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from aexlutils import logger
from settings import SETTINGS
from custom_prompt_template import DynamicPromptTemplate
from utils import OpenAIQuery
import json
from pydantic import BaseModel, Field

class DynamicPromptInput(BaseModel):
    parameter: list = Field(description = "User required parameter for creating prediction prompt.")

class DynamicPromptTool(BaseTool):
    name = "Create dynamic prompt"
    description = """
        useful when you need to make a new prompt for query to predict horse race ranking.
        You should understand user's requirement on betting and enter the parameters used for the prompt 
        output will be a whole new prompt version in string.
        """
    args_schema: Type[BaseModel] = DynamicPromptInput

    def _run(self, parameter: list):
        response = get_dynamic_prompt(parameter)
        return response

    def _arun(self, parameter: list):
        raise NotImplementedError("get_dynamic_prompt does not support async")

# Helper function
def generate_full_prompt(parameter: list) -> str:
    prompt = DynamicPromptTemplate.create_prompt_template(
        parameter=parameter
      )
    return prompt

def get_dynamic_prompt(parameter: list) -> str:
    # Read gain loss json
    logger.info("Generating Dynamic Prompt for ranking")
    prompt = generate_full_prompt(parameter)
    response = OpenAIQuery.generate_response(prompt) 
    return response
