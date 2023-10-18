from typing import List, Dict, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class RankingEvent(BaseModel):
    race_date: date
    race_num: int = Field(ge=1, le=14)
    ranking: List[int] = Field(ge=1, le=14)
    top2_ranking: List[int] = Field(ge=1, le=14)
    all_race_reborn: dict
    cold_race_reborn: dict
    reborn: List[int]
    reborn_1: List[int]
    reborn_3: List[int]
    deselect: List[int]
    historical_reborn: List[int]
    roadmap_ranking: List[int]
    explanation: Dict[str, str] = {}
    distribution: Dict[str, str] = {}
    prompt: Dict[str, str]
    minute: int
    update_ts: datetime
    update_ts_explanation: Optional[datetime] = None
