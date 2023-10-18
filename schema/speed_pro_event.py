from typing import List, Dict
from datetime import date, datetime
from pydantic import BaseModel, Field


class SpeedProEvent(BaseModel):
    race_date: date
    race_num: int = Field(ge=1, le=14)
    update_ts: datetime
    statistic: dict

