from typing import Union
from datetime import date, datetime
from pydantic import BaseModel, Field


class RaceCardEvent(BaseModel):
    race_date: date
    race_num: int = Field(ge=1, le=14)
    race_time: datetime
    revised_race_time: datetime
    update_ts: datetime
    race_class: str
    name: str
    venue: str
    track: str
    track_condition: Union[str, None]
    course: Union[str, None]
    distance: int
    prize: int
    horses: list
