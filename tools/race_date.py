import re
import time
import openai
import pandas as pd
from typing import List, Optional, Type
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from aexlutils import logger
from settings import SETTINGS
from utils import OpenAIQuery
import json
from pydantic import BaseModel, Field
from utils.oss import OssFetcher

class RaceDateTool(BaseTool):
    name = "Get all race date"
    description = """
        useful when you need to get available horse race date.
        You don't have to enter anything
        output will be a list of all available horse race date.
        """
    # return_direct: bool = True

    def _run(self):
        response = get_race_date()
        return response

    def _arun(self):
        raise NotImplementedError("get_race_date does not support async")

# Helper function

def get_race_date() -> Optional[str]:
    """If you don't have race dates, use this tool to get all race dates. Helpful to find the earliest or latest race date."""
    paths = OssFetcher.get_paths_of_all_objects_in_directory_from_event_store('prod/racecards/')
    race_dates = []
    for path in paths:
        race_date = path.split('prod/racecards/')[1].split('/')[0]
        if race_date not in race_dates:
            race_dates.append(race_date)
    return f'Here are all race dates in ascending order (from earliest to latest): {race_dates}.'
