import asyncio
import os
import shutil
from pathlib import Path
from functools import lru_cache

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.src.db import models

from app.src.api.app_depends import get_session, get_static_image_path
from tests.config import IMAGE_PATH, REMOVE_FILES, STATIC_PATH, TESTS_DB


async def create_all(engine, Base, models: list):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await prepare_test_models(engine, models)


async def drop_all(engine, Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def prepare_test_models(engine, models):
    session = sessionmaker(engine, class_=AsyncSession)()
    for model in models:
        session.add(model)
    await session.commit()
    await session.close()


@pytest.fixture
def first_user():
    return models.User(id=1, name="TEST_NAME", api_key="test")


@pytest.fixture
def environments():
    os.environ["DATABASE"] = "DB"
    os.environ["DATABASE_USER"] = "USER"
    os.environ["DEBUG"] = "1"
    os.environ["DATABASE_PASSWORD"] = "pass"
    os.environ["DATABASE_URL"] = 'localhost'
    yield
    os.environ.pop("DATABASE")
    os.environ.pop("DATABASE_USER")
    os.environ.pop("DEBUG")
    os.environ.pop("DATABASE_PASSWORD")
    os.environ.pop("DATABASE_URL")


@pytest.fixture
def db_engine(first_user):
    TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TESTS_DB}"
    _test_engine = create_async_engine(TEST_DATABASE_URL)

    user_A = models.User(id=2, name="TEST2_NAME", api_key="test2")
    user_B = models.User(id=3, name="TEST3_NAME", api_key="test3")
    asyncio.run(
        create_all(_test_engine, models.Base, [first_user, user_A, user_B])
    )

    yield _test_engine

    asyncio.run(drop_all(_test_engine, models.Base))
    if REMOVE_FILES:
        os.remove(TESTS_DB)


@pytest.fixture
def session_maker(db_engine):
    return sessionmaker(db_engine, expire_on_commit=True, class_=AsyncSession)


@pytest.fixture
def session_depends(session_maker):
    async def get_test_db_session():
        session = session_maker()
        try:
            yield session
        finally:
            await session.close()

    return get_test_db_session


@pytest.fixture
def static_path():
    async def get_static_path():
        path = Path(STATIC_PATH)
        path.mkdir(exist_ok=True, parents=True)
        return path

    yield get_static_path
    if REMOVE_FILES:
        shutil.rmtree(Path(STATIC_PATH), ignore_errors=True)
        shutil.rmtree(Path(IMAGE_PATH), ignore_errors=True)


@lru_cache
@pytest.fixture
def app(session_depends, static_path, environments):
    from app.src.api.app import app as _app
    _app.dependency_overrides[get_session] = session_depends
    _app.dependency_overrides[get_static_image_path] = static_path
    yield _app


@pytest.fixture
def client(app):
    client = TestClient(app=app)
    yield client
    from tests.factories import session

    session.close()
