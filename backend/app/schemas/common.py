from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class IntentType(str, Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK_STATUS = "UPDATE_TASK_STATUS"
    QUERY_TASKS = "QUERY_TASKS"
    GENERAL_NOTE = "GENERAL_NOTE"


class NoteSource(str, Enum):
    VOICE = "voice"
    TEXT = "text"
