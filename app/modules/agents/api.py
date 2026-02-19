from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.agents.schemas import (
    AgentHeartbeatIn,
    AgentHeartbeatOut,
    AgentMetricsIn,
    AgentProcessesIn,
    AgentCommandResultIn,
    AgentCommandAckIn,
)
from app.modules.agents.service import AgentsService
from app.redis.events import publish_to_pc_channel

router = APIRouter(prefix="/agent", tags=["agent"])

def get_service() -> AgentsService:
    return AgentsService()

@router.post("/heartbeat", response_model=AgentHeartbeatOut)
async def heartbeat(
    hb: AgentHeartbeatIn,
    session: AsyncSession = Depends(get_session),
    svc: AgentsService = Depends(get_service),
):
    commands, now_ts = await svc.handle_heartbeat(session, hb)
    return {"server_ts": now_ts, "commands": commands}

@router.post("/metrics")
async def push_metrics(
    data: AgentMetricsIn,
    svc: AgentsService = Depends(get_service),
):
    await svc.handle_metrics(data)
    return {"ok": True}

@router.post("/processes")
async def push_processes(
    data: AgentProcessesIn,
    svc: AgentsService = Depends(get_service),
):
    await svc.handle_processes(data)
    return {"ok": True}

@router.post("/command_ack")
async def command_ack(
    payload: AgentCommandAckIn,
    session: AsyncSession = Depends(get_session),
    svc: AgentsService = Depends(get_service),
):
    await svc.handle_command_ack(session, payload)

    await publish_to_pc_channel(str(payload.pc_id), {
        "pc_id": str(payload.pc_id),
        "type": "command_update",
        "command_id": str(payload.command_id),
        "status": "acknowledged",
        "ts": payload.ts,
    })
    
    return {"ok": True}

@router.post("/command_result")
async def command_result(
    payload: AgentCommandResultIn,
    session: AsyncSession = Depends(get_session),
    svc: AgentsService = Depends(get_service),
):
    await svc.handle_command_result(session, payload)

    await publish_to_pc_channel(str(payload.pc_id), {
        "pc_id": str(payload.pc_id),
        "type": "command_update",
        "command_id": str(payload.command_id),
        "status": payload.status,              # completed/failed
        "exit_code": payload.exit_code,
        "finished_at_ts": payload.finished_at_ts,
    })
    
    return {"ok": True}
