from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator
from langchain_core.output_parsers import JsonOutputParser


class Event(BaseModel):
    title: str = Field(description="Title of the event")
    description: str = Field(description="Description of the event")
    start_date: datetime = Field(
        description="Start date of the event. Must be in the format %Y-%m-%dT%H:%M:%S"
    )
    end_date: datetime = Field(
        description="End date of the event. Must be in the format %Y-%m-%dT%H:%M:%S"
    )
    location: str = Field(description="Location of the event")
    other_info: Optional[str] = Field(description="Other information about the event")
    event_type: Optional[str] = Field(description="Event type")

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def convert_str2datetime(cls, v: str, info: ValidationInfo):
        try:
            return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
        except:
            raise ValueError(
                f"{info.field_name} must be a string in the format %Y-%m-%dT%H:%M:%S"
            )

    @field_validator("end_date", mode="after")
    @classmethod
    def check_future_end_date(cls, v: datetime):
        if v < datetime.now():
            raise ValueError("`end_date` must be in the future")
        return v

    @model_validator(mode="after")
    def check_date_rage(self):
        if self.end_date <= self.start_date:
            raise ValueError("`end_date` must be grater than `start_date`")
        return self


class OutputCreateEvent(BaseModel):
    clarification: Optional[str] = Field(description="Question to ask the user")
    event: Optional[Event] = Field(description="The event to be created")


output_parser = JsonOutputParser(pydantic_object=OutputCreateEvent)
