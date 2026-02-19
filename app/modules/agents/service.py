from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.computers import ComputersRepo
from app.db.repositories.commands import CommandsRepo
from app.modules.agents.schemas import (
    AgentHeartbeatIn,
    AgentMetricsIn,
    AgentProcessesIn,
    AgentCommandResultIn,
    AgentCommandAckIn,
    AgentCommandOut,
)
from app.redis.state_repo import PcStateRepo


class AgentsService:
    def __init__(self):
        self.state_repo = PcStateRepo()
        self.computers_repo = ComputersRepo()
        self.commands_repo = CommandsRepo()

    async def handle_heartbeat(self, session: AsyncSession, hb: AgentHeartbeatIn):
        pc_id_str = str(hb.pc_id)

        # 1) Redis online + meta
        meta_payload: dict[str, object] = {}
        if hb.hostname is not None: 
            meta_payload["hostname"] = hb.hostname
        if hb.os_name is not None: 
            meta_payload["os_name"] = hb.os_name
        if hb.os_version is not None: 
            meta_payload["os_version"] = hb.os_version
        if hb.os_build is not None: 
            meta_payload["os_build"] = str(hb.os_build)
        if hb.username is not None: 
            meta_payload["username"] = hb.username
        if hb.ip is not None: 
            meta_payload["ip"] = hb.ip
        if hb.mac is not None: 
            meta_payload["mac"] = hb.mac
        if hb.agent_version is not None: 
            meta_payload["agent_version"] = hb.agent_version

        if meta_payload:
            await self.state_repo.upsert_meta(pc_id_str, meta_payload, seq=hb.seq)
        else:
            await self.state_repo.touch_online(pc_id_str, seq=hb.seq)

        # 2) Postgres ensure + update partial
        await self.computers_repo.ensure_exists(session, hb.pc_id)

        updates: dict[str, object] = {}
        if hb.hostname: 
            updates["hostname"] = hb.hostname
        if hb.mac: 
            updates["mac"] = hb.mac
        if hb.os_name: 
            updates["os_name"] = hb.os_name
        if hb.os_version: 
            updates["os_version"] = hb.os_version
        if hb.os_build is not None: 
            updates["os_build"] = str(hb.os_build)
        if hb.ip: 
            updates["ip"] = hb.ip
        if hb.username: 
            updates["username"] = hb.username
        if hb.agent_version: 
            updates["agent_version"] = hb.agent_version

        if updates:
            await self.computers_repo.update_meta_partial(session, hb.pc_id, updates)

        now = datetime.now(timezone.utc)

        # 3) Commands: взять pending, пометить sent, вернуть в ответ
        cmds = await self.commands_repo.pull_pending_for_agent(session, hb.pc_id, limit=30, now=now)
        await self.commands_repo.mark_sent(session, [c.id for c in cmds], now)
        await session.commit()

        out_cmds = [AgentCommandOut.model_validate(c) for c in cmds]
        return out_cmds, int(now.timestamp())

    async def handle_metrics(self, data: AgentMetricsIn) -> None:
        await self.state_repo.upsert_metrics(
            str(data.pc_id),
            {"cpu": data.cpu, "ram": data.ram, "disk": data.disk},
            seq=data.seq,
        )

    async def handle_processes(self, data: AgentProcessesIn) -> None:
        await self.state_repo.upsert_processes(str(data.pc_id), data.items, seq=data.seq)

    async def handle_command_ack(self, session: AsyncSession, ack: AgentCommandAckIn) -> None:
        now = datetime.now(timezone.utc)
        await self.commands_repo.mark_acked(session, ack.command_id, now)
        await session.commit()

    async def handle_command_result(self, session: AsyncSession, res: AgentCommandResultIn) -> None:
        now = datetime.now(timezone.utc)
        await self.commands_repo.save_result(
            session,
            command_id=res.command_id,
            status=res.status,
            stdout=res.stdout,
            stderr=res.stderr,
            exit_code=res.exit_code,
            meta=None,
            now=now,
        )
        await session.commit()
