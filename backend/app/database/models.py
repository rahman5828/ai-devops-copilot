from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    service: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    container: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    impact: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    root_cause: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    root_cause_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    signals: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    timeline: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    alternative_hypotheses: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    recommendations: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    @staticmethod
    def serialize_json(value: object) -> str:
        return json.dumps(value)

    @staticmethod
    def deserialize_json(value: str) -> object:
        return json.loads(value)
