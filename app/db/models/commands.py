import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, Integer, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Command(Base):
    __tablename__ = "commands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    pc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("computers.id", ondelete="CASCADE"),
        index=True,
    )

    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # ✅ lowercase always
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True, default="pending")

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    expected_pc_ver: Mapped[int | None] = mapped_column(Integer, nullable=True)

    result: Mapped["CommandResult | None"] = relationship(back_populates="command", uselist=False)


Index("ix_commands_pc_pending", Command.pc_id, Command.status, Command.created_at)


class CommandResult(Base):
    __tablename__ = "command_results"

    command_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commands.id", ondelete="CASCADE"),
        primary_key=True,
    )

    status: Mapped[str] = mapped_column(String(32), nullable=False)  
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    command: Mapped["Command"] = relationship(back_populates="result")
