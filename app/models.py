"""Data models and data access (C7)."""
from datetime import datetime, timezone

from flask import current_app, g
from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    create_engine,
    event,
)
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

EMAIL_MAX = 254
TITLE_COLUMN_LENGTH = 100
DESCRIPTION_COLUMN_LENGTH = 1000


def utcnow():
    """Naive UTC timestamp (SQLite does not store time zones)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(UserMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )

    def get_id(self):
        return str(self.id)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_owner_id", "owner_id"),
        Index("ix_tasks_owner_id_title", "owner_id", "title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(TITLE_COLUMN_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(
        String(DESCRIPTION_COLUMN_LENGTH), nullable=False, default=""
    )
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    owner: Mapped[User] = relationship(back_populates="tasks")


def _py_lower(value):
    """Unicode-aware lower-casing for SQLite (its lower() is ASCII only)."""
    return value.lower() if isinstance(value, str) else value


def _build_url(app):
    url = app.config.get("DATABASE_URL")
    if url:
        return url
    return URL.create("sqlite", database=str(app.instance_path + "/tasks.db"))


def init_db(app):
    """Create the engine, register helpers, create tables (no migrations)."""
    # hide_parameters keeps bound values (emails, hashes) out of error messages/logs.
    engine = create_engine(_build_url(app), hide_parameters=True)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _on_connect(dbapi_connection, _record):
            dbapi_connection.create_function("py_lower", 1, _py_lower, deterministic=True)
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(engine)
    app.extensions["db_engine"] = engine
    app.extensions["session_factory"] = sessionmaker(engine, expire_on_commit=False)
    app.teardown_appcontext(_close_session)


def get_session():
    """Request-scoped session."""
    if "db_session" not in g:
        g.db_session = current_app.extensions["session_factory"]()
    return g.db_session


def _close_session(_exc=None):
    session = g.pop("db_session", None)
    if session is not None:
        session.close()
