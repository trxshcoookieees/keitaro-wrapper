from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StreamOffer(Base):
    __tablename__ = "stream_offers"

    __table_args__ = (
        UniqueConstraint(
            "stream_id",
            "offer_id",
            name="uq_stream_offer",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stream_id: Mapped[int] = mapped_column(
        ForeignKey("streams.id"),
        index=True,
    )

    offer_id: Mapped[int] = mapped_column(Integer)
    offer_name: Mapped[str] = mapped_column(String(255))

    share: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)

    stream: Mapped["Stream"] = relationship(back_populates="offers")