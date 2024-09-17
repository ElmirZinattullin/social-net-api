from typing import Annotated

from fastapi import Depends, Header, HTTPException

from ..db import crud, models
from ..db.database import AsyncSession, get_db_session

STATIC_PATH = "static"


async def get_session():
    # print("session start")
    session = get_db_session()()
    try:

        # with session.begin():
        yield session
    # print("close_session")
    finally:
        await session.close()


async def get_user(
    api_key: Annotated[
        str, Header(..., description="api-key for user authentication")
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
):

    try:
        user = await crud.get_one(models.User, session, api_key=api_key)
    except crud.CRUDException:
        raise HTTPException(status_code=401, detail="Wrong api-key")
    return user


async def get_static_image_path():
    path = STATIC_PATH
    # path = f'{path}'
    yield path


Session = Annotated[AsyncSession, Depends(get_session)]
User = Annotated[models.User, Depends(get_user)]
Static_image_path = Annotated[str, Depends(get_static_image_path)]
