import random
import uuid
import os
import utils.aws_utils as aws_utils

from datetime import datetime, timedelta
from utils.models.model_utils import Event

SQS_QUEUE_EVENTS_ARN = os.getenv("SQS_QUEUE_EVENTS_ARN", "")
IAM_ROLE_EVENT_SCHEDULER_ARN = os.getenv("IAM_ROLE_EVENT_SCHEDULER_ARN", "")


def create_schedule(event: Event):
    event_id = str(uuid.uuid4())
    now = datetime.now()
    cron_expressions: list[dict] = [
        {
            "cron": f"at({(event.start_date - timedelta(days=30)).strftime('%Y-%m-%dT10:{0}:00').format(str(random.randint(0, 59)).zfill(2))})",
            "name": "FirstStoryBeforeEvent",
            # l'end_date serve solo a evitare di creare un schedule che non avrà esecuzione.
            # In ogni caso questo campo non viene usato nello schedule
            "end_date": max((event.start_date - timedelta(days=30)), now),
        },
        {
            "cron": "rate(7 days)",
            "name": "EvenStoriesBeforeEvent",
            "start_date": max(
                (event.start_date - timedelta(days=25)).replace(
                    hour=11, minute=random.randint(0, 59)
                ),
                now,
            ),
            "end_date": max((event.start_date - timedelta(days=4)), now),
        },
        {
            "cron": "rate(7 days)",
            "name": "OddStoriesBeforeEvent",
            "start_date": max(
                (event.start_date - timedelta(days=22)).replace(
                    hour=11, minute=random.randint(0, 59)
                ),
                now,
            ),
            "end_date": max((event.start_date - timedelta(days=8)), now),
        },
        {
            "cron": "rate(1 days)",
            "name": "DailyBeforeEvent",
            "start_date": max(
                (event.start_date - timedelta(days=1) - timedelta(hours=4)), now
            ),
            "end_date": max(event.start_date, now),
        },
    ]

    aws_utils.create_schedule_group(
        schedule_group_name=event_id,
        tags=[
            {"Key": "event_type", "Value": event.event_type},
            {
                "Key": "event_date",
                "Value": event.start_date.strftime("%Y-%m-%dT%H:%M"),
            },
        ],
    )

    for ce in cron_expressions:
        if ce.get("end_date") == now:
            continue
        aws_utils.create_schedule(
            name_schudeler=ce["name"],
            schedule_expression=ce["cron"],
            target_arn=SQS_QUEUE_EVENTS_ARN,
            role_arn=IAM_ROLE_EVENT_SCHEDULER_ARN,
            start_date=ce.get("start_date", datetime.now()),
            end_date=ce.get("end_date", datetime.max),
            event=event,
            schedule_group_name=event_id,
        )
