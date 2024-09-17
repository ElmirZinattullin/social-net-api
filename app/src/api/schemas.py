from typing import Annotated, List

from fastapi import Body, File, UploadFile, status
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Short information about the user"""

    id: int = Body(
        ...,
        ge=1,
        title="ID",
        description="User's identifier",
        examples=[1, 2, 3],
    )
    name: str = Body(
        ...,
        description="User's name",
        examples=["Ivan Ivanovich", "Petr Petrovich"],
    )
    model_config = ConfigDict(from_attributes=True)
    #
    # class Config:
    #     from_attributes = True


class MediaID(BaseModel):
    """Media file identifier"""

    id: int = Body(
        ...,
        ge=1,
        title="ID",
        description="media file identifier",
        examples=[1, 2, 3],
    )


class UserExtensive(User):
    """Extensive information about the user"""

    followers: List["User"] = Body([], description="User's followers list")
    following: List["User"] = Body([], description="User's following list")


class Result(BaseModel):
    """Result of request processing"""

    result: bool = Body(
        ..., description="The status of processing", examples=[True]
    )


class Error(Result):
    """Message about error in request processing"""

    error_type: str = Body(..., description="Error type")
    error_message: str = Body(..., description="Error message")


class UserResult(Result):
    """User info"""

    user: UserExtensive = Body(
        ...,
        title="User Model",
        description="User's info with followers and following",
    )


#
# class MeAnswer(UserAnswer):
#     ...


class TweetCreateResult(Result):
    """Tweet create result"""

    tweet_id: int = Body(
        ...,
        ge=1,
        title="ID",
        description="Tweet's identifier",
        examples=[1, 2, 3],
    )


class MediaPostResult(Result):
    media_id: int = Body(
        ...,
        ge=1,
        title="ID",
        description="Media file's identifier",
        examples=[1, 2, 3],
    )


class MediaPost(BaseModel):
    file: Annotated[UploadFile, File(..., description="Upload image")]


class TweetsResult(Result):
    """Tweets list"""

    tweets: List["Tweet"] = Body([], description="Tweets list")


class User_v2(BaseModel):
    """Short information about the user"""

    user_id: int = Body(
        ...,
        ge=1,
        title="ID",
        description="User's identifier",
        examples=[1, 2, 3],
    )
    name: str = Body(
        ...,
        description="User's name",
        examples=["Ivan Ivanovich", "Petr Petrovich"],
    )
    model_config = ConfigDict(from_attributes=True)


class Tweet(BaseModel):
    """Information about the tweet"""

    id: int = Body(
        ...,
        ge=1,
        title="ID",
        description="Tweet's identifier",
        examples=[1, 2, 3],
    )
    content: str = Body(
        ...,
        title="tweet's content",
        description="tweet body",
        examples=[1, 2, 3],
    )
    attachments: List[str] = Body(
        ...,
        description="list of links to media files",
        examples=[["/static/1/some image.jpg"]],
    )
    author: "User" = Body(..., description="Author of tweet")
    likes: List["User_v2"] = Body(
        [], description="List of users who liked the tweet"
    )
    model_config = ConfigDict(from_attributes=True)


class TweetCreate(BaseModel):
    """Tweet Create data"""

    tweet_data: str = Body(..., min_length=1, description="tweet message")
    tweet_media_ids: List[
        Annotated[
            int,
            Body(
                ...,
                ge=1,
                title="ID",
                description="Media file's identifier",
                examples=[1, 2, 3],
            ),
        ]
    ] = Body(
        None,
        description="List of media files identifiers",
        examples=[
            [1, 2, 3],
        ],
    )


error_responses = {
    status.HTTP_403_FORBIDDEN: {"model": Error},
    status.HTTP_400_BAD_REQUEST: {"model": Error},
    status.HTTP_401_UNAUTHORIZED: {"model": Error},
}
