from enum import Enum


class ChatOrchestratorState(Enum):
    ADD_EVENT = 1
    DELETE_EVENT = 2
    MANAGE_EVENT_IMAGES = 3
    CREATE_STORY = 4
    CREATE_POST = 5

    SELECTING_ACTION = 99
    END = 100


class ChatAddEventState(Enum):
    ADD_EVENT = 1
    EVENT_INFO = 2
    RECAP = 3
