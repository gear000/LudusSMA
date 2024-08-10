from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator


class Event(BaseModel):
    title: str = Field(description="Title of the event", title="Titolo")
    description: str = Field(
        description="Description of the event. It should't contain references to location or time and should be long 5/6 words or less",
        title="Descrizione",
    )
    start_date: datetime = Field(
        description="Start date of the event. Must be in the format %Y-%m-%dT%H:%M:%S",
        title="Data di inizio",
    )
    end_date: datetime = Field(
        description="End date of the event. Must be in the format %Y-%m-%dT%H:%M:%S and must be after `start_date`",
        title="Data di fine",
    )
    location: str = Field(description="Location of the event", title="Luogo")
    other_info: Optional[str] = Field(
        description="Other information about the event", title="Altre informazioni"
    )
    event_type: Optional[str] = Field(
        description="The type of event organised, such as tournaments or special evenings",
        title="Tipo di evento",
    )

    def format_for_tg_message(self) -> str:
        """
        Helper function for formatting the gathered user info.

        ### Returns ###
            str: The formatted string.

        ### Output Example ###

        ```
         - <b>Titolo</b>: <value>
         - <b>Descrizione</b>: <value>
         - <b>Data di inizio</b>: <value>
         - <b>Data di fine</b>: <value>
         - <b>Ora di inizio</b>: <value>
         - <b>Ora di fine</b>: <value>
         - <b>Luogo</b>: <value>
         - <b>Altre informazioni</b>: <value>
        ```
        """

        EVENT_KEYS = {
            "title": "Titolo",
            "description": "Descrizione",
            "start_date": "Data di inizio",
            "end_date": "Data di fine",
            "start_time": "Ora di inizio",
            "end_time": "Ora di fine",
            "location": "Luogo",
            "other_info": "Altre informazioni",
        }

        event_data: dict = self.model_dump()

        event_data["start_time"] = event_data["start_date"].time()
        event_data["start_date"] = event_data["start_date"].date()

        event_data["end_time"] = event_data["end_date"].time()
        event_data["end_date"] = event_data["end_date"].date()

        facts = [f"<b>{EVENT_KEYS[key]}</b>: {event_data[key]}" for key in EVENT_KEYS]
        return "\n\n - " + "\n - ".join(facts)

    def format_for_tg_message_(self) -> str:
        data = self.model_dump()
        return "\n - ".join(
            [
                f"<b>{field.title()}</b>: {data[key]}"
                for key, field in self.model_fields.values()
            ]
        )

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def convert_str2datetime(cls, v: str | datetime, info: ValidationInfo):
        try:
            if isinstance(v, str):
                return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S")
            elif isinstance(v, datetime):
                return v
        except:
            raise ValueError(
                f"{info.field_name} must be a string in the format %Y-%m-%dT%H:%M:%S or a datetime object"
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
