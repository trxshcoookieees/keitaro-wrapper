from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Stream(Base):
    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    keitaro_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"),
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50), default="regular")
    schema: Mapped[str] = mapped_column(String(50), default="landings")
    action_type: Mapped[str] = mapped_column(String(50), default="http")
    action_payload: Mapped[str | None] = mapped_column(String, nullable=True)

    filter_or: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dirty: Mapped[bool] = mapped_column(Boolean, default=False)

    filters: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="streams")
    offers: Mapped[list["StreamOffer"]] = relationship(
        back_populates="stream",
        cascade="all, delete-orphan",
    )