from __future__ import annotations
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AgentCommandAckIn(BaseModel):
    pc_id: UUID
    command_id: UUID
    ts: Optional[int] = None


class AgentHeartbeatIn(BaseModel):
    pc_id: UUID
    seq: int = Field(ge=0)

    hostname: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    os_build: str | float | int | None = None
    username: str | None = None
    ip: str | None = None
    mac: str | None = None
    agent_version: str | None = None


class AgentMetricsIn(BaseModel):
    pc_id: UUID
    seq: int = Field(ge=0)
    cpu: int = Field(ge=0, le=100)
    ram: int = Field(ge=0, le=100)
    disk: int = Field(ge=0, le=100)


class AgentProcessesIn(BaseModel):
    pc_id: UUID
    seq: int = Field(ge=0)
    items: list[dict[str, Any]] = Field(default_factory=list)


class AgentCommandOut(BaseModel):
    id: UUID
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class AgentHeartbeatOut(BaseModel):
    server_ts: float
    commands: List[AgentCommandOut] = Field(default_factory=list)


class AgentCommandResultIn(BaseModel):
    pc_id: UUID
    command_id: UUID
    status: str  
    exit_code: int = 0
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    finished_at_ts: Optional[int] = None
