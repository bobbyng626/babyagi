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

class RankingActualInput(BaseModel):
    race_date: str = Field(description="The race date of a horse race")
    race_num: int = Field(description="The race number of a horse race")
    
class RankingActualTool(BaseTool):
    name = "Get race actual ranking"
    description = """
        useful when you need to get the actual ranking of a horse race.
        You should enter the horse race date and horse race number of the race
        output will be a list of the actual ranking by horse number.
        """
    args_schema: Type[BaseModel] = RankingActualInput

    def _run(self, race_date: str, race_num: int):
        response = get_race_actual_ranking(race_date, race_num)
        return response

    def _arun(self, race_date: str, race_num: int):
        raise NotImplementedError("get_race_actual_ranking does not support async")

# Helper function

def get_race_actual_ranking(race_date: str, race_num: int) -> Optional[str]:
    result = OssFetcher.read_json_from_event_store(f'prod/results/confirmed/{race_date}/{race_num}.json', True)
    if result is None:
        return None
    try:
        ranking = result['dividend_odds']['quartet'][0]['combination']
        return f'Actual ranking or result of race {race_num} on {race_date}: {ranking}'
    except Exception as ex:
        logger.error('Error in getting quartet combination:', ex)
        return None
