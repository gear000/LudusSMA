import random
from utils import aws_utils


def create_schedulers():
    cron_expression = [
        {
            "cron": f"cron({random.randint(0,59)} 16 ? * TUE,FRI *)",
            "name": "EveryThreeDaysBeforeEvent",
            "delta_time": "",
        },
        {
            "cron": f"cron({random.randint(0,59)} 16 ? * TUE,THU,SAT,SUN *)",
            "name": "AlternateDaysBeforeEvent",
        },
        {
            "cron": f"cron({random.randint(0,59)} 16 ? * * *)",
            "name": "DailyBeforeEvent",
        },
    ]

    for ce in cron_expression:
        pass
