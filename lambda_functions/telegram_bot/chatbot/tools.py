import uuid
import os
from datetime import datetime, timedelta
from utils import aws_utils

SQS_QUEUE_EVENTS_ARN = os.getenv("SQS_QUEUE_EVENTS_ARN", "")
IAM_ROLE_EVENT_SCHEDULER_ARN = os.getenv("IAM_ROLE_EVENT_SCHEDULER_ARN", "")


def create_schedulers(event_scheduler: dict, event_date: datetime = datetime.now()):
    event_id = str(uuid.uuid4())
    now = datetime.now()
    cron_expression: list[dict] = [
        {
            "cron": f"at({(event_date - timedelta(days=30)).strftime('%Y-%m-%dT10:00:00')})",
            "name": f"{event_id}-FistStoryBeforeEvent",
        },
        {
            "cron": "rate(7 days)",
            "name": f"{event_id}-EvenStoriesBeforeEvent",
            "start_date": max((event_date - timedelta(days=25)), now),
            "end_date": max((event_date - timedelta(days=4)), now),
        },
        {
            "cron": "rate(7 days)",
            "name": f"{event_id}-OddStoriesBeforeEvent",
            "start_date": max((event_date - timedelta(days=22)), now),
            "end_date": max((event_date - timedelta(days=8)), now),
        },
        {
            "cron": f"rate(1 days)",
            "name": f"{event_id}-DailyBeforeEvent",
            "start_date": max(
                (event_date - timedelta(days=1) - timedelta(hours=4)), now
            ),
            "end_date": max(event_date, now),
        },
    ]

    for ce in cron_expression:
        if ce.get("end_date") == now:
            continue
        aws_utils.create_scheduler(
            name_schudeler=ce["name"],
            schedule_expression=ce["cron"],
            target_arn=SQS_QUEUE_EVENTS_ARN,
            role_arn=IAM_ROLE_EVENT_SCHEDULER_ARN,
            input=event_scheduler,
            start_date=ce.get("start_date"),
            end_date=ce.get("end_date"),
        )
