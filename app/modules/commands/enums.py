from enum import StrEnum

class CommandStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    ACKED = "acked"
    COMPLETED = "completed"
    FAILED = "failed"
