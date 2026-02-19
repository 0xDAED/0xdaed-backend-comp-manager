from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.computers import Computer

class ComputersRepo:
    async def ensure_exists(self, session: AsyncSession, pc_id):
        res = await session.execute(select(Computer.id).where(Computer.id == pc_id))
        if res.scalar_one_or_none() is None:
            session.add(Computer(id=pc_id))
            await session.commit()

    async def update_meta(
        self,
        session: AsyncSession,
        pc_id,
        *,
        hostname: str | None,
        mac: str | None,
        os_name: str | None,
        os_version: str | None,
        os_build: str | None,
        ip: str | None,
        username: str | None,
    ):
        await session.execute(
            update(Computer)
            .where(Computer.id == pc_id)
            .values(
                hostname=hostname,
                mac=mac,
                os_name=os_name,
                os_version=os_version,
                os_build=os_build,
                ip=ip,
                username=username,
            )
        )
        await session.commit()

    async def update_meta_partial(self, session, pc_id, updates: dict):
        if not updates:
            return

        await session.execute(
            update(Computer)
            .where(Computer.id == pc_id)
            .values(**updates)
        )
