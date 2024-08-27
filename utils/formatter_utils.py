import os
from utils.aws_utils import list_s3_folders

_S3_BUCKET_IMAGES_NAME = os.getenv("S3_BUCKET_IMAGES_NAME")


def format_event_types() -> list[str]:
    return [
        elem.strip("/").split("/")[-1].title()
        for elem in list_s3_folders(_S3_BUCKET_IMAGES_NAME, "clean-images/")
    ]
