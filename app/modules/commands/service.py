from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.commands import Command  

class CommandsService:
    async def create(self, session: AsyncSession, payload):
        cmd = Command(
            pc_id=payload.pc_id,
            type=payload.type,
            payload=payload.payload,
            status="pending",
        )
        session.add(cmd)
        await session.commit()
        await session.refresh(cmd)
        return cmd
