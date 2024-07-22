import datetime
from pydantic import BaseModel


class Event(BaseModel):
    title: str
    description: str
    start_date: datetime
    end_date: datetime
    event_type: str
    location: str
    other_info: str
