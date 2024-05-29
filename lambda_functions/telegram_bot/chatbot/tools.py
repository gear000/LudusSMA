import uuid
import random
from datetime import datetime, timedelta
from utils import aws_utils


class _EventScheduler:
    def __init__(self, name, cron, start_date, end_date):
        self.name = name
        self.cron = cron
        self.start_date = start_date
        self.end_date = end_date

    @classmethod
    def from_dict(cls, d: dict):
        name = d.get("name")
        return cls(name, d["cron"], d["start_date"], d["end_date"])


def create_schedulers(event_scheduler: dict, event_date: datetime):

    event_scheduler: _EventScheduler = _EventScheduler.from_dict(event_scheduler)
    event_id = str(uuid.uuid4())

    cron_expression = [
        {
            "cron": f"at({(event_date - timedelta(days=30)).strftime('%Y-%m-%dT%10:00:00')})",
            "name": f"{event_id}-FistStoryBeforeEvent",
        },
        {
            "cron": "rate(7 days)",
            "name": f"{event_id}-EvenStoriesBeforeEvent",
            "start_date": (event_date - timedelta(days=25)).strptime(
                "%Y-%m-%d 00:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            "end_date": (event_date - timedelta(days=4)).strptime(
                "%Y-%m-%d 00:00:00", "%Y-%m-%d %H:%M:%S"
            ),
        },
        {
            "cron": "rate(7 days)",
            "name": f"{event_id}-OddStoriesBeforeEvent",
            "start_date": (event_date - timedelta(days=22)).strptime(
                "%Y-%m-%d 00:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            "end_date": (event_date - timedelta(days=8)).strptime(
                "%Y-%m-%d 00:00:00", "%Y-%m-%d %H:%M:%S"
            ),
        },
        {
            "cron": f"rate(1 days)",
            "name": f"{event_id}-DailyBeforeEvent",
            "start_date": (event_date - timedelta(days=1) - timedelta(hours=4)),
            "end_date": event_date,
        },
    ]

    for ce in cron_expression:
        pass
