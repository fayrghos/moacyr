from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from core.utils import Timestamp, to_timestamp


class Bind(SQLModel, table=True):
    __tablename__ = "binds"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    text: str
    author: int = Field(index=True)
    guild: int = Field(index=True)

    created: datetime = Field(default_factory=datetime.now)
    updated: Optional[datetime] = Field(default=None)

    @property
    def f_created(self) -> str:
        return to_timestamp(int(self.created.timestamp()), Timestamp.Relative)

    @property
    def f_updated(self) -> str:
        if not self.updated:
            return "Nunca"
        return to_timestamp(int(self.updated.timestamp()), Timestamp.Relative)
