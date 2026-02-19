from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentCommandOut(BaseModel):
    id: UUID
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_orm_command(cls, c) -> "AgentCommandOut":
        return cls(id=c.id, type=c.type, payload=c.payload or {})

class RunCmdPayload(BaseModel):
    cmd: str
    timeout_seconds: int | None = 60
    run_as_admin: bool | None = False

class RunScriptPayload(BaseModel):
    language: str = Field(description="powershell|cmd|python|...")
    script: str
    timeout_seconds: int | None = 120

class KillProcessPayload(BaseModel):
    pid: int
    create_time: float | None = None  
    force: bool = True

class BlockProcessPayload(BaseModel):
    exe_path: str
    enabled: bool = True

class CreateCommandIn(BaseModel):
    pc_id: UUID
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    expected_pc_ver: int | None = None

class CreateCommandOut(BaseModel):
    id: UUID

class TaskDto(BaseModel):
    id: str
    pc_id: str
    type: str
    status: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    acked_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @classmethod
    def from_orm_command(cls, c) -> "TaskDto":
        return cls(
            id=str(c.id),
            pc_id=str(c.pc_id),
            type=c.type,
            status=str(c.status),
            payload=c.payload or {},
            created_at=getattr(c, "created_at", None),
            sent_at=getattr(c, "sent_at", None),
            acked_at=getattr(c, "acked_at", None),
            finished_at=getattr(c, "finished_at", None),
        )
