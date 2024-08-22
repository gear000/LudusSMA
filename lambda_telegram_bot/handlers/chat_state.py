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
    ADD_EVENT = 1
    EVENT_INFO = 2
    RECAP = 3
    SET_NEW_EVENT_TYPE = 4
    LOAD_IMAGE = 5


class ChatManageEventTypeState(Enum):
    ADD_IMAGE = 1
    ADD_EVENT_TYPE = 2
    RECAP = 3
    SET_NEW_EVENT_TYPE = 4
    LOAD_IMAGE = 5
