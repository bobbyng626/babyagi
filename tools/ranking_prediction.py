import re
import time
import openai
import pandas as pd
from aexlutils import logger
from typing import List, Type
from langchain.prompts import PromptTemplate 
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
# from schema import LlmVersionsMapping
from utils import OpenAIQuery

from custom_prompt_template import BANKER_Version5, BANKER_Version10, LEG_Version9, LEG_Version10, LEG_Version11
from settings import SETTINGS

class RankingPredictionInput(BaseModel):
    race_date: str = Field(description = "Race date in YYYY-MM-DD format")
    race_num: int = Field(description = "Race number as an integer")
    prompt_version: str = Field(description = "Indicator to choose the prompt version")

class RankingPredictionTool(BaseTool):
    name = "Get race predicted ranking"
    description = """
        useful when you need to rank a horse race to get the predicted ranking. 
        You should enter the horse race date and horse race num for the required query ranking.
        You should enter the prompt version to decide how to rank the horse race
        output with a list of ranking of all horses in the race.
        """
    args_schema: Type[BaseModel] = RankingPredictionInput

    def _run(self, race_date: str, race_num: int, prompt_version: str):
        response = get_race_predicted_ranking(race_date, race_num, prompt_version)
        return response

    def _arun(self, race_date: str, race_num: int, prompt_version: str):
        raise NotImplementedError("get_race_predicted_ranking does not support async")
    
# Helper function
def extract_ranking_from_response(response: str) -> List[int]:
    ranking = response.split('EXPLANATION:')[0].strip()
    horse_pattern = r'Horse (\d+)'
    horses = re.findall(horse_pattern, ranking)
    ranking = []
    for horse in horses:
        if horse not in ranking:
            ranking.append(int(horse))
    return ranking


def ask_for_ranking_using_prompt(prompt: str) -> List[int]:
    response = OpenAIQuery.generate_response(prompt)
    if len(response) == 0:
        logger.info(f"Failed to get correct response")
        return []
    ranking = extract_ranking_from_response(response)
    return ranking

def get_race_predicted_ranking(race_date: str, race_num: int, prompt_version: str) -> str:
    logger.info(f"Getting race predicted ranking for race {race_date}_{race_num}, with prompt version {prompt_version} ")
    llm_prompt_versions_dict = {
        "banker_5": BANKER_Version5,
        "banker_10": BANKER_Version10,
        "leg_9": LEG_Version9,
        "leg_10": LEG_Version10,
        "leg_11": LEG_Version11
    }
    if prompt_version not in llm_prompt_versions_dict:
        return f'Prompt version is invalid, get another prompt version and query the prediction later.'
    # prompt_version_constructor = llm_prompt_versions_dict[prompt_version]
    # prompt = prompt_version_constructor.full_prompt_generator(race_date, race_num, 0)
    # ranking = ask_for_ranking_using_prompt(prompt)
    # return f'Predicted ranking using version {prompt_version} of race {race_num} on {race_date}: {ranking}.'

    ranking =[1,2,3,4,5,6,7,8]
    return f'Predicted ranking using version {prompt_version} of race {race_num} on {race_date}: {ranking}.'


