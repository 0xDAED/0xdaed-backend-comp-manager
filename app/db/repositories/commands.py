from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, func, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.commands import Command, CommandResult
from app.modules.commands.enums import CommandStatus


class CommandsRepo:
    async def get_by_id(self, session: AsyncSession, command_id: UUID) -> Command | None:
        res = await session.execute(select(Command).where(Command.id == command_id))
        return res.scalar_one_or_none()

    async def pull_pending_for_agent(self, session: AsyncSession, pc_id: UUID, limit: int, now: datetime):
        q = (
            select(Command)
            .where(
                Command.pc_id == pc_id,
                Command.status == CommandStatus.PENDING,
                or_(Command.expires_at.is_(None), Command.expires_at > now),
            )
            .order_by(Command.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        res = await session.execute(q)
        return list(res.scalars().all())

    async def mark_sent(self, session: AsyncSession, command_ids: list[UUID], now: datetime) -> None:
        if not command_ids:
            return
        await session.execute(
            update(Command)
            .where(Command.id.in_(command_ids))
            .values(status=CommandStatus.SENT, sent_at=now)
        )

    async def mark_acked(self, session: AsyncSession, command_id: UUID, now: datetime) -> None:
        await session.execute(
            update(Command)
            .where(Command.id == command_id)
            .values(status=CommandStatus.ACKED, acked_at=now)
        )

    async def save_result(
        self,
        session: AsyncSession,
        *,
        command_id: UUID,
        status: str,  # completed/failed
        stdout: str | None,
        stderr: str | None,
        exit_code: int | None,
        meta: dict | None,
        now: datetime,
    ) -> None:
        await session.execute(
            update(Command)
            .where(Command.id == command_id)
            .values(
                status=CommandStatus.COMPLETED if status == CommandStatus.COMPLETED else CommandStatus.FAILED,
                finished_at=now,
            )
        )

        stmt = (
            insert(CommandResult)
            .values(
                command_id=command_id,
                status=status,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                meta=meta,
            )
            .on_conflict_do_update(
                index_elements=[CommandResult.command_id],
                set_=dict(
                    status=status,
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    meta=meta,
                    created_at=func.now(),
                ),
            )
        )
        await session.execute(stmt)

    async def list_recent_by_pc_ids(self, session: AsyncSession, pc_ids: list[UUID], limit_per_pc: int = 20):
        if not pc_ids:
            return {}

        q = (
            select(Command)
            .where(Command.pc_id.in_(pc_ids))
            .order_by(Command.created_at.desc())
            .limit(len(pc_ids) * limit_per_pc)
        )
        res = await session.execute(q)
        rows = list(res.scalars().all())

        out: dict[UUID, list[Command]] = defaultdict(list)
        for c in rows:
            if len(out[c.pc_id]) < limit_per_pc:
                out[c.pc_id].append(c)
        return out
