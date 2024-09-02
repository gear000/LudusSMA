import os
from utils.aws_utils import list_s3_folders

_S3_BUCKET_IMAGES_NAME = os.getenv("S3_BUCKET_IMAGES_NAME")


def format_event_types() -> list[str]:
    return [
        elem.strip("/").split("/")[-1].title()
        for elem in list_s3_folders(_S3_BUCKET_IMAGES_NAME, "clean-images/")
    ]


def format_tags(tags: list[dict[str, str]]) -> dict[str, str]:
    """
    funzione con lo scopo di formattare i tags delle risorse in un dizionario a cui posso accedere direttamente per chiave.

    ### Parameters ###
    tags: list[dict[str, str]]
        lista di dizionari che contengono le chiavi e i valori dei tag.

    ### Returns ###
    format_tags: dict[str, str]
        dizionario con le chiavi e i valori dei tag formattati.

    ### Example ###
    >>> tags = [
            {
                "Key": "event_type",
                "Value": "sport",
            },
            {
                "Key": "event_date",
                "Value": "2022-01-01",
            },
        ]

    >>> format_tags(tags)
    {'event_date': '2022-01-01', 'event_type': 'sport'}

    """
    return {tag["Key"]: tag["Value"] for tag in tags}
