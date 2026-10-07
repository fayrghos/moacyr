"""Database access layer for binds."""

from datetime import UTC, datetime

from sqlmodel import Session, col, delete, select

from core.database import dbengine
from core.models.bind import Bind


class BindManager:
    def single(self, title: str, guild: int) -> Bind | None:
        """Fetch a single bind by title and guild."""
        with Session(dbengine) as session:
            results = session.exec(
                select(Bind)
                .where(
                    col(Bind.title) == title,
                    col(Bind.guild) == guild,
                )
                .limit(1)
            )
            return results.first()

    def many_server(self, guild: int, cur: str, amount: int) -> tuple[Bind, ...]:
        """Fetch server binds matching the current input."""
        with Session(dbengine) as session:
            results = session.exec(
                select(Bind)
                .where(
                    col(Bind.guild) == guild,
                    col(Bind.title).startswith(cur),
                )
                .limit(amount)
                .order_by(Bind.title)
            )
            return tuple(results.all())

    def many_author(
        self, author: int, guild: int, cur: str, amount: int
    ) -> tuple[Bind, ...]:
        """Fetch author binds matching the current input."""
        with Session(dbengine) as session:
            results = session.exec(
                select(Bind)
                .where(
                    col(Bind.author) == author,
                    col(Bind.guild) == guild,
                    col(Bind.title).startswith(cur),
                )
                .limit(amount)
                .order_by(Bind.title)
            )
            return tuple(results.all())

    def add(self, bind: Bind) -> None:
        """Insert a new bind record."""
        with Session(dbengine) as session:
            session.add(bind)
            session.commit()

    def edit(self, bind: Bind) -> None:
        """Update an existing bind record."""
        with Session(dbengine) as session:
            bind.updated = datetime.now(UTC)
            session.merge(bind)
            session.commit()

    def delete(self, bind: Bind) -> None:
        """Delete a single bind record."""
        with Session(dbengine) as session:
            session.delete(bind)
            session.commit()

    def nuke(self, guild: int) -> None:
        """Delete all binds from a specific guild."""
        with Session(dbengine) as session:
            session.exec(delete(Bind).where(col(Bind.guild) == guild))
            session.commit()
