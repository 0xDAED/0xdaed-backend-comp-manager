from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.modules.commands.schemas import CreateCommandIn, CreateCommandOut, TaskDto
from app.modules.commands.service import CommandsService

router = APIRouter(prefix="/ui/commands", tags=["commands"])

def get_service() -> CommandsService:
    return CommandsService()

@router.post("", response_model=CreateCommandOut)
async def create_command(
    payload: CreateCommandIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    svc: CommandsService = Depends(get_service),
):
    try:
        cmd = await svc.create(session, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    broker = getattr(request.app.state, "ws_broker", None)
    if broker:
        task = TaskDto.from_orm_command(cmd).model_dump(mode="json")
        await broker.send_to_pc(str(payload.pc_id), {"type": "task_update", "pc_id": str(payload.pc_id), "task": task})

    return CreateCommandOut(id=cmd.id)
