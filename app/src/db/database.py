import logging
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database():
    from ..settings import (
        DATABASE,
        DATABASE_PASSWORD,
        DATABASE_USER,
        DATABASE_URL,
    )

    if DATABASE and DATABASE_USER and DATABASE_PASSWORD and DATABASE_URL:
        database_connection = (
            f"postgresql+asyncpg://"
            f"{DATABASE_USER}:{DATABASE_PASSWORD}"
            f"@{DATABASE_URL}:5432/{DATABASE}"
        )
    else:
        raise Exception("NO FOUND ONE ORE MORE ENVIRONMENTS")
    return database_connection


# DATABASE_URL = f"sqlite+aiosqlite:///test.db"


@lru_cache
def get_engine():
    logging.warning("get_engine_func_start")
    return create_async_engine(get_database(), echo=False)


@lru_cache
def get_db_session():
    return sessionmaker(
        get_engine(), expire_on_commit=True, class_=AsyncSession
    )
