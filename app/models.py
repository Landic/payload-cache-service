from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TransformationCache(Base):
    __tablename__ = "transformation_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    transformed_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class Payload(Base):
    __tablename__ = "payloads"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_payload_fingerprint"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
