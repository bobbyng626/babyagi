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

class RaceNumberInput(BaseModel):
    race_date: str = Field(description="The race date of a horse race")
    
class RaceNumberTool(BaseTool):
    name = "Get number of race"
    description = """
        useful when you need to get number of horse race in one race date.
        You should enter the horse race date
        output will be a list of all number of horse race in one horse race date.
        """
    # return_direct: bool = True
    def _run(self, race_date: str):
        response = get_number_of_races_in_race_day(race_date)
        return response

    def _arun(self):
        raise NotImplementedError("get_race_date does not support async")

# Helper function
def get_number_of_races_in_race_day(race_date: str) -> int:
    """If you have race date, use this tool to get the number of races on that race day."""
    number_of_races = len(
        OssFetcher.get_paths_of_all_objects_in_directory_from_event_store(f'prod/racecards/{race_date}/')
    )
    return f'There are {number_of_races} races on {race_date}. The last race is race {number_of_races}.'
