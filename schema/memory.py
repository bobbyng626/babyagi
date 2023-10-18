from typing import List, Dict
from enum import Enum, auto
from pydantic import BaseModel
from datetime import date, datetime


class MemoryKeyPrefix(str, Enum):
    RACE_CARD = auto()
    RACE_CARD_RECORD = auto()
    RESULT_RECORD = auto()
    INVESTMENT_SNAPSHOT = auto()
    ROADMAP_SCORE = auto()
    WIN_PLACE_ODDS_SCORE = auto()
    DECISION_TREE_RECORD = auto()
    WIN_PLACE_CI_SCORE = auto()
    QUINELLA_WIN_CI_SCORE = auto()
    SPEED_PRO = auto()
    COLD_DOOR = auto()
    POOL_RATIO = auto()
    EXPECTED_WIN_RECORD = auto()
    LOSS_DETAIL = auto()

    DECISION_TREE = auto()
    RACE_HORSE_MAPPING = auto()
    LLM_RANKING = auto()
    LLM_PROMPT = auto()
    ROADMAP_RANKING = auto()


class RaceCardRecord(BaseModel):
    race_date: date = ""
    race_num: List[int] = []
    race_time: List[datetime] = []
    horses: List[Dict] = []


class DecisionTreeRecord(BaseModel):
    race_date: date = ""
    race_num: List[int] = []
    race_time: List[datetime] = []
    horses: List[Dict] = []


class RaceHorseMapping(BaseModel):
    race_date: date = ""
    race_num: List[int] = []
    horse_mapping: Dict[str, List[str]] = {}
    all_horse_code_list: List[str] = []
