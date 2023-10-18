from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import List, Dict


class DecisionTreeEvent(BaseModel):
    race_date: date
    race_num: int = Field(ge=1, le=14)
    reborn: Dict[str, List]
    eliminated: List[int]
    update_ts: datetime
    # Can add other levels when needed

