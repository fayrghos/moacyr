from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, Index, SQLModel

from core.utils import Timestamp, to_timestamp


class Bind(SQLModel, table=True):
    __tablename__ = "binds"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    text: str
    author: int
    guild: int

    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated: Optional[datetime] = Field(default=None)

    __table_args__ = (
        Index("ix_binds_pairs", "guild", "title", unique=True),
        Index("ix_binds_completes", "guild", "author", "title"),
    )

    @property
    def f_created(self) -> str:
        return to_timestamp(int(self.created.timestamp()), Timestamp.Relative)

    @property
    def f_updated(self) -> str:
        if not self.updated:
            return "Nunca"
        return to_timestamp(int(self.updated.timestamp()), Timestamp.Relative)
