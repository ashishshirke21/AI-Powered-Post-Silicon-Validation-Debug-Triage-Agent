from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RunRow(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    source: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    line_count: Mapped[int] = mapped_column(Integer, default=0)
    # Raw log text, stored so a run can be re-analyzed.
    raw_log: Mapped[str] = mapped_column(Text, default="")
    # Serialized TriageReport JSON, populated after analysis.
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
