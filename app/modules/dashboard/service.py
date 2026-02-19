from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.computers import Computer
from app.db.repositories.commands import CommandsRepo
from app.modules.commands.schemas import TaskDto
from app.redis.state_repo import PcStateRepo


class DashboardService:
    def __init__(self):
        self.state_repo = PcStateRepo()
        self.commands_repo = CommandsRepo()

    async def get_pcs(self, session: AsyncSession) -> dict:
        res = await session.execute(select(Computer))
        pcs = list(res.scalars().all())
        pc_ids = [pc.id for pc in pcs]

        tasks_map = await self.commands_repo.list_recent_by_pc_ids(session, pc_ids, limit_per_pc=20)

        computers_out = []
        for pc in pcs:
            pc_id_str = str(pc.id)
            state = await self.state_repo.get_state(pc_id_str)

            metrics = state.get("metrics") or {}
            procs = state.get("procs") or {}
            online = bool(state.get("online", False))

            tasks_models = tasks_map.get(pc.id, [])
            tasks = [TaskDto.from_orm_command(t).model_dump(mode="json") for t in tasks_models]

            dto = {
                "id": pc_id_str,
                "computerActive": online,
                "computerName": pc.hostname or pc_id_str,
                "computerMacAddress": pc.mac or "—",
                "lastTimeActive": "0 мин назад" if online else "—",
                "cpu": {"value": int(metrics.get("cpu", 0) or 0)},
                "ozu": {"value": int(metrics.get("ram", 0) or 0)},
                "hard_drive": {"value": int(metrics.get("disk", 0) or 0)},
                "processes": f"{len((procs.get('items') or []))} процессов",
                "processList": (procs.get("items") or [])[:300],
                "system": {
                    "osName": pc.os_name,
                    "osVersion": pc.os_version,
                    "osBuild": pc.os_build,
                    "ip": pc.ip,
                    "username": pc.username,
                },
                "tasks": tasks,
            }
            computers_out.append(dto)

        return {"computers": computers_out}
