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

class TaskListInput(BaseModel):
    prompt: str = Field(description="A question or query from user")

class TaskListTool(BaseTool):
    name = "Generate task list tool"
    description = """
        useful when you need to generate the task list for ranking a horse race.
        """
    args_schema: Type[BaseModel] = TaskListInput

    def _run(self, prompt: str):
        response = get_task_list(prompt)
        return response

    def _arun(self, prompt: str):
        raise NotImplementedError("get_task_list does not support async")

def get_task_list(prompt: str) -> str:
    # Read gain loss json
    logger.info("Waiting for response...")
    # response = OpenAIQuery.generate_response(prompt) 
    response = """
1. Get horse race date and race number
2. Predict the ranking of the horse race on 2023-10-01 race number 2
3. Output the predicted ranking of the horse race to race to user
4. Output the actual ranking of the horse race to user
"""
    return response
