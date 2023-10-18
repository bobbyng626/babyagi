from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import List, Dict


class ExpectedWinEvent(BaseModel):
    race_date: date
    race_num: int = Field(ge=1, le=14)
    expected_win_odds: dict
    update_ts: datetime
    # Can add other levels when needed

