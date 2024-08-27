from enum import Enum


class ChatOrchestratorState(Enum):
    ADD_EVENT = 1
    DELETE_EVENT = 2
    MANAGE_EVENT_TYPE = 3
    CREATE_STORY = 4
    CREATE_POST = 5

    SELECTING_ACTION = 99
    END = 100


class ChatAddEventState(Enum):
    EVENT_INFO = 1
    RECAP = 2


class ChatManageEventTypeState(Enum):
    SET_NEW_EVENT_TYPE = 1
    LOAD_IMAGE = 2
    UPDATING_ACTION = 3
    DELETING = 4
