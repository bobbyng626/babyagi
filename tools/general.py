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

class GeneralInput(BaseModel):
    prompt: str = Field(description="A general question or query from user")

class GeneralTool(BaseTool):
    name = "General tool"
    description = """
        useful when you need to do general question answering or action.
        It can relate to any topics and question, just a normal and general query.
        """
    args_schema: Type[BaseModel] = GeneralInput

    def _run(self, prompt: str):
        response = get_general_response(prompt)
        return response

    def _arun(self, prompt: str):
        raise NotImplementedError("get_general_response does not support async")

def get_general_response(prompt: str) -> str:
    # Read gain loss json
    logger.info("Waiting for response...")
    response = OpenAIQuery.generate_response(prompt) 
    return response
