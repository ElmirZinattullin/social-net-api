from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Path, Request, UploadFile, status
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    StarletteHTTPException,
)
from fastapi.responses import JSONResponse

from ..settings import DEBUG
from . import schemas
from ..db import crud, models, database
from .app_depends import Session, Static_image_path, User
from .customopenapi import custom_openapi
from ..services.file_service import write_to_disk

tags_metadata = [
    {
        "name": "TWEETS",
        "description": "Endpoints for tweets.",
    },
    {
        "name": "USERS",
        "description": "Endpoints for users.",
    },
    {
        "name": "MEDIAS",
        "description": "Endpoints for medias.",
    },
]
description = "API for twitter-clone"


@asynccontextmanager
async def database_init(app: FastAPI):
    engine = database.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    tags_metadata=tags_metadata, debug=DEBUG, lifespan=database_init
)


@app.middleware("http")
async def session_close(request: Request, call_next):
    response = await call_next(request)
    try:
        await request.state.session.close()
    except AttributeError:
        ...
    return response


@app.exception_handler(RequestValidationError)
async def http_validation_exception_handler(request, exc):
    msg = str(exc)
    code = status.HTTP_400_BAD_REQUEST
    if "api-key" in msg:
        msg = 'Authentication failed. Request doesn\'t have "api-key" header. '
        code = status.HTTP_401_UNAUTHORIZED
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=msg
    )
    return JSONResponse(answer.model_dump(), code)


@app.exception_handler(crud.InstanceNotExists)
async def http_instance_not_exist_exception_handler(request, exc):
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=str(exc)
    )
    return JSONResponse(answer.model_dump(), status.HTTP_404_NOT_FOUND)


@app.exception_handler(crud.CRUDException)
async def http_crud_exception_handler(request, exc):
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=str(exc)
    )
    return JSONResponse(answer.model_dump(), status.HTTP_403_FORBIDDEN)


@app.exception_handler(HTTPException)
async def http_http_exception_handler(request, exc):
    msg = str(exc)
    code = exc.status_code
    if "api-key" in msg:
        msg = 'Authentication failed. Request doesn\'t have "api-key" header. '
        code = status.HTTP_401_UNAUTHORIZED
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=msg
    )
    return JSONResponse(answer.model_dump(), code)


@app.exception_handler(StarletteHTTPException)
async def http_all_exception_handler(request, exc):
    msg = str(exc)
    code = exc.status_code
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=msg
    )
    return JSONResponse(answer.model_dump(), code, headers=exc.headers)


@app.get(
    "/users/me",
    response_model=schemas.UserResult,
    response_model_exclude_none=True,
    tags=["USERS"],
    status_code=status.HTTP_200_OK,
    responses=schemas.error_responses,
)
async def get_me(
    request: Request, session: Session, user: User
) -> schemas.UserResult:
    """Endpoint for get the information about an authenticated users"""
    user_schema = schemas.UserExtensive.model_validate(user)
    return schemas.UserResult(result=True, user=user_schema)


@app.post(
    "/tweets",
    response_model=schemas.TweetCreateResult,
    tags=["TWEETS"],
    status_code=status.HTTP_201_CREATED,
    responses=schemas.error_responses,
)
async def post_tweet(
    request: Request, tweet: schemas.TweetCreate, session: Session, user: User
) -> schemas.TweetCreateResult:
    """Endpoint for create a tweet"""
    new_tweet = models.Tweet(
        content=tweet.tweet_data,
        author=user,
        images=tweet.tweet_media_ids if tweet.tweet_media_ids else [],
    )
    tweet_id = await crud.save(new_tweet, session)
    await session.commit()
    return schemas.TweetCreateResult(result=True, tweet_id=tweet_id)


@app.post(
    "/medias",
    response_model=schemas.MediaPostResult,
    tags=["MEDIAS"],
    status_code=status.HTTP_201_CREATED,
    responses=schemas.error_responses,
)
async def post_image(
    request: Request,
    file: Annotated[
        UploadFile, File(..., description="image file", title="FILE")
    ],
    session: Session,
    user: User,
    static_path: Static_image_path,
) -> schemas.MediaPostResult:
    """Endpoint for post an image"""
    path = await write_to_disk(user, file, static_path)
    new_image = models.Image(path=path)
    media_id = await crud.save(new_image, session)
    await session.commit()
    return schemas.MediaPostResult(result=True, media_id=media_id)


@app.get(
    "/tweets",
    response_model=schemas.TweetsResult,
    response_model_exclude_none=True,
    tags=["TWEETS"],
    responses=schemas.error_responses,
)
async def get_tweets(
    request: Request, session: Session, user: User
) -> schemas.TweetsResult:
    """Endpoint for get all tweets"""
    tweets = await crud.get_following_tweets(user, session)
    tweets_schema = [
        schemas.Tweet.model_validate(tweet) for tweet in tweets.unique()
    ]
    return schemas.TweetsResult(result=True, tweets=tweets_schema)


@app.delete(
    "/tweets/{id}",
    response_model=schemas.Result,
    tags=["TWEETS"],
    responses=schemas.error_responses.update(
        {status.HTTP_404_NOT_FOUND: {"models": schemas.Error}}
    ),
)
async def delete_tweet(
    request: Request,
    session: Session,
    user: User,
    tweet_id: Annotated[
        int,
        Path(
            ...,
            alias="id",
            title="Id of the tweet.",
            description="Номер айди",
        ),
    ],
) -> schemas.Result:
    """Endpoint for delete the tweet. Only author can delete the tweet"""
    await crud.delete_tweet(tweet_id, user, session)
    await session.commit()
    return schemas.Result(result=True)


@app.get(
    "/users/{id}",
    response_model=schemas.UserResult,
    response_model_exclude_none=True,
    tags=["USERS"],
    responses=schemas.error_responses.update(
        {status.HTTP_404_NOT_FOUND: {"models": schemas.Error}}
    ),
)
async def get_user(
    request: Request,
    session: Session,
    user: User,
    user_id: Annotated[
        int,
        Path(
            ...,
            alias="id",
            title="Id of the user.",
            description="Номер пользователя",
        ),
    ],
) -> schemas.UserResult:
    """Endpoint for get the information about the user by user's id."""
    find_user = await crud.get_by_id(
        models.User, user_id, session, populate_existing=True
    )
    user_schema = schemas.UserExtensive.model_validate(find_user)
    return schemas.UserResult(result=True, user=user_schema)


@app.post(
    "/tweets/{id}/likes",
    response_model=schemas.Result,
    response_model_exclude_none=True,
    tags=["TWEETS"],
    status_code=status.HTTP_201_CREATED,
    responses=schemas.error_responses.update(
        {status.HTTP_404_NOT_FOUND: {"models": schemas.Error}}
    ),
)
async def like_tweet(
    request: Request,
    session: Session,
    user: User,
    tweet_id: Annotated[
        int,
        Path(
            ...,
            alias="id",
            title="Id of the tweet.",
            description="Номер твита",
        ),
    ],
) -> schemas.Result:
    """Endpoint for like the tweet. it will cause an error message
    if user will like the tweet repeatedly"""
    tweet = await crud.get_by_id(models.Tweet, tweet_id, session)
    try:
        await crud.get_one(
            models.Like, session, user_id=user.id, tweet_id=tweet.id
        )
        raise HTTPException(400, "Like is already exist")
    except crud.CRUDException:
        new_like = models.Like(user_id=user.id, tweet_id=tweet.id)
    await crud.save(new_like, session)
    await session.commit()
    return schemas.Result(result=True)


@app.delete(
    "/tweets/{id}/likes",
    response_model=schemas.Result,
    response_model_exclude_none=True,
    tags=["TWEETS"],
    responses=schemas.error_responses.update(
        {status.HTTP_404_NOT_FOUND: {"models": schemas.Error}}
    ),
)
async def delete_like_tweet(
    request: Request,
    session: Session,
    user: User,
    tweet_id: Annotated[
        int,
        Path(
            ...,
            alias="id",
            title="Id of the tweet.",
            description="Номер твита",
        ),
    ],
) -> schemas.Result:
    """Endpoint for delete user's like to the tweet."""
    tweet = await crud.get_by_id(models.Tweet, tweet_id, session)
    like = await crud.get_one(
        models.Like, session, user_id=user.id, tweet_id=tweet.id
    )
    await crud.delete(like, session)
    await session.commit()
    return schemas.Result(result=True)


@app.post(
    "/users/{id}/follow",
    response_model=schemas.Result,
    response_model_exclude_none=True,
    tags=["USERS"],
    status_code=status.HTTP_201_CREATED,
    responses=schemas.error_responses.update(
        {status.HTTP_404_NOT_FOUND: {"models": schemas.Error}}
    ),
)
async def follow_user(
    request: Request,
    session: Session,
    user: User,
    following_user_id: Annotated[
        int,
        Path(
            ...,
            alias="id",
            title="Id of the user.",
            description="Номер пользователя",
        ),
    ],
) -> schemas.Result:
    """Endpoint for following the user.
    it will cause an error message if user will follow the user repeatedly"""
    following_user = await crud.get_by_id(
        models.User, following_user_id, session
    )
    if user == following_user:
        raise HTTPException(400, "You can't following self")
    try:
        follower = await crud.get_one(
            models.Follower,
            session,
            user_id=user.id,
            following_id=following_user.id,
        )
        raise HTTPException(400, "You are already following")
    except crud.CRUDException:
        follower = models.Follower(user=user, following=following_user)
    await crud.save(follower, session)
    await session.commit()
    return schemas.Result(result=True)


@app.delete(
    "/users/{id}/follow",
    response_model=schemas.Result,
    response_model_exclude_none=True,
    tags=["USERS"],
    responses=schemas.error_responses.update(
        {status.HTTP_404_NOT_FOUND: {"models": schemas.Error}}
    ),
)
async def delete_follow_user(
    request: Request,
    session: Session,
    user: User,
    following_user_id: Annotated[
        int,
        Path(
            ...,
            alias="id",
            title="Id of the user.",
            description="Номер пользователя",
        ),
    ],
) -> schemas.Result:
    """Endpoint for stop following the user."""
    following_user = await crud.get_by_id(
        models.User, following_user_id, session
    )
    follower = await crud.get_one(
        models.Follower,
        session,
        user_id=user.id,
        following_id=following_user.id,
    )
    await crud.delete(follower, session)
    await session.commit()
    return schemas.Result(result=True)


custom_openapi(app)
