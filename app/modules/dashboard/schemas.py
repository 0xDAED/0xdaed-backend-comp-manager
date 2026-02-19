from pydantic import BaseModel
from typing import List

class CpuRamDisk(BaseModel):
    value: int


class SystemInfo(BaseModel):
    osName: str | None = None
    osVersion: str | None = None
    osBuild: str | None = None
    ip: str | None = None
    username: str | None = None


class ProcessDto(BaseModel):
    pid: int | None = None
    name: str | None = None
    cpu: int | None = None
    memoryMb: int | None = None
    status: str | None = None
    blocked: bool = False

class TaskDto(BaseModel):
    id: str
    type: str
    status: str           
    title: str | None = None
    progress: int | None = None
    createdAtTs: float | None = None

class ComputerDto(BaseModel):
    id: str
    computerActive: bool
    computerName: str
    computerMacAddress: str
    lastTimeActive: str
    processes: str

    cpu: CpuRamDisk
    ozu: CpuRamDisk
    hard_drive: CpuRamDisk

    system: SystemInfo
    processList: List[ProcessDto] = []
    tasks: List[TaskDto] = []

class DashboardResponse(BaseModel):
    computers: List[ComputerDto]
