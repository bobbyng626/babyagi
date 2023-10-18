from datetime import date, datetime
from pydantic import BaseModel, Field


class LossDetailEvent(BaseModel):
    race_date: date
    race_num: int = Field(ge=1, le=14)
    loss_results: dict
    update_ts: datetime
    # Can add other levels when needed

