from typing import Optional

from sqlmodel import Session, select

from core.database import dbengine
from core.models.bind import Bind


class BindManager:
    def single(self, title: str, guild: int) -> Optional[Bind]:
        """Fetches a single bind."""
        with Session(dbengine) as session:
            results = session.exec(
                select(Bind).where(Bind.title == title, Bind.guild == guild).limit(1)
            )
            return results.first()

    def add(self, bind: Bind) -> None:
        """Inserts a single bind."""
        with Session(dbengine) as session:
            session.add(bind)
            session.commit()

    def edit(self, bind: Bind) -> None:
        """Updates a bind."""
        with Session(dbengine) as session:
            session.merge(bind)
            session.commit()

    def delete(self, bind: Bind) -> None:
        """Deletes a bind."""
        with Session(dbengine) as session:
            session.delete(bind)
            session.commit()

    def nuke(self, guild: int) -> None:
        """Deletes all binds from a especific guild."""
        with Session(dbengine) as session:
            results = session.exec(select(Bind).where(Bind.guild == guild))
            for item in results:
                session.delete(item)
            session.commit()
