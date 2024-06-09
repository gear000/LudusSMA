from pydantic import BaseModel


class EventScheduler(BaseModel):
    title: str
    description: str
    date: str
    time: str
    event_type: str
    location: str
    other_info: str
