import uuid
import os
from datetime import datetime, timedelta
from utils.aws_utils import create_scheduler
from utils.models.model_utils import Event

SQS_QUEUE_EVENTS_ARN = os.getenv("SQS_QUEUE_EVENTS_ARN", "")
IAM_ROLE_EVENT_SCHEDULER_ARN = os.getenv("IAM_ROLE_EVENT_SCHEDULER_ARN", "")


def create_schedulers(event: Event):
    event_id = str(uuid.uuid4())
    now = datetime.now()
    cron_expressions: list[dict] = [
        {
            "cron": f"at({(event.start_date - timedelta(days=30)).strftime('%Y-%m-%dT10:00:00')})",
            "name": f"{event_id}-FirstStoryBeforeEvent",
            # l'end_date serve solo a evitare di creare un scheduler che non avrà esecuzione.
            # In ogni caso questo campo non viene usato nello scheduler
            "end_date": max((event.start_date - timedelta(days=30)), now),
        },
        {
            "cron": "rate(7 days)",
            "name": f"{event_id}-EvenStoriesBeforeEvent",
            "start_date": max((event.start_date - timedelta(days=25)), now),
            "end_date": max((event.start_date - timedelta(days=4)), now),
        },
        {
            "cron": "rate(7 days)",
            "name": f"{event_id}-OddStoriesBeforeEvent",
            "start_date": max((event.start_date - timedelta(days=22)), now),
            "end_date": max((event.start_date - timedelta(days=8)), now),
        },
        {
            "cron": f"rate(1 days)",
            "name": f"{event_id}-DailyBeforeEvent",
            "start_date": max(
                (event.start_date - timedelta(days=1) - timedelta(hours=4)), now
            ),
            "end_date": max(event.start_date, now),
        },
    ]

    for ce in cron_expressions:
        if ce.get("end_date") == now:
            continue
        create_scheduler(
            name_schudeler=ce["name"],
            schedule_expression=ce["cron"],
            target_arn=SQS_QUEUE_EVENTS_ARN,
            role_arn=IAM_ROLE_EVENT_SCHEDULER_ARN,
            start_date=ce.get("start_date", ""),
            end_date=ce.get("end_date", ""),
            event=event,
        )
