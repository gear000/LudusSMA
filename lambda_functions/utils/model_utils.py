import datetime
from pydantic import BaseModel


class Event(BaseModel):
    title: str
    description: str
    startdate: datetime
    enddate: datetime
    event_type: str
    location: str
    other_info: str
