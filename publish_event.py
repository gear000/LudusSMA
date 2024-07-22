import boto3
import uuid
from datetime import datetime, timedelta


def create_schedule(name, schedule_expression, sqs_queue_arn, start_date, end_date):
    client = boto3.client("scheduler")

    # Creating the schedule
    response = client.create_schedule(
        ActionAfterCompletion="DELETE",
        Name=name,
        ScheduleExpression=schedule_expression,
        StartDate=start_date,
        EndDate=end_date,
        State="ENABLED",
        FlexibleTimeWindow={"MaximumWindowInMinutes": 10, "Mode": "FLEXIBLE"},
        Target={
            "Arn": sqs_queue_arn,
            "RoleArn": "arn:aws:iam::730335476244:role/LudusSMA-deployment-stack-LudusSMALambdaRole-nsnEXb2TcQLq",
            "Input": f'{{"uuid": "{str(uuid.uuid4())}"}}',
        },
    )
    print(f"Created schedule with ARN: {response['ScheduleArn']}")


def main(event_datetime):
    sqs_queue_arn = "arn:aws:sqs:eu-west-1:730335476244:ScheduledEvents"
    event_id = str(uuid.uuid4())

    # Adjust these dates to fit the scheduling requirements
    three_weeks_before = max(event_datetime - timedelta(weeks=3), datetime.now())
    one_month_before = max(event_datetime - timedelta(days=30), datetime.now())

    # Every day at 16:00, one week before the event
    daily_expression = "cron(0 16 ? * * *)"
    create_schedule(
        f"{event_id}-DailyBeforeEvent",
        daily_expression,
        sqs_queue_arn,
        event_datetime - timedelta(days=7),
        event_datetime,
    )

    # Every other day, two to three weeks before the event
    alternate_days_expression = "cron(0 16 ? * MON,WED,FRI *)"
    try:
        create_schedule(
            name=f"{event_id}-AlternateDaysBeforeEvent",
            schedule_expression=alternate_days_expression,
            sqs_queue_arn=sqs_queue_arn,
            start_date=three_weeks_before,
            end_date=max(event_datetime - timedelta(weeks=1), datetime.now()),
        )
    except Exception as e:
        print("Error in AlternateDaysBeforeEvent")
        print(f"Exception: {e}")
        print("Arguments:")
        print(f"\tname: {event_id}-AlternateDaysBeforeEvent")
        print(f"\tschedule_expression: {alternate_days_expression}")
        print(f"\tstart_date: {three_weeks_before}")
        print(f"\tend_date: {max(event_datetime - timedelta(days=14), datetime.now())}")

    # Every three days, three weeks to a month before the event
    every_three_days_expression = "cron(0 16 ? * TUE,FRI *)"
    try:
        create_schedule(
            name=f"{event_id}-EveryThreeDaysBeforeEvent",
            schedule_expression=every_three_days_expression,
            sqs_queue_arn=sqs_queue_arn,
            start_date=one_month_before,
            end_date=three_weeks_before,
        )
    except Exception as e:
        print("Error in EveryThreeDaysBeforeEvent")
        print(f"Exception: {e}")
        print("Arguments:")
        print(f"\tname: {event_id}-AlternateDaysBeforeEvent")
        print(f"\tschedule_expression: {every_three_days_expression}")
        print(f"\tstart_date: {one_month_before}")
        print(f"\tend_date: {three_weeks_before}")


if __name__ == "__main__":
    event_date = datetime(2024, 7, 1)  # Example: Set your event date
    main(event_date)
