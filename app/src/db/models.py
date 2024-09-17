from typing import Any, Dict, List

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Image(AsyncAttrs, Base):
    __tablename__ = "images"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String())
    tweets_association: Mapped[List["TweetsImage"]] = relationship(
        back_populates="image",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    tweets: AssociationProxy[List["Tweet"]] = association_proxy(
        "tweets_association",
        "tweet",
    )


class Tweet(AsyncAttrs, Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String())
    author_id: Mapped["int"] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    author: Mapped["User"] = relationship(lazy="joined")
    likes_association: Mapped[List["Like"]] = relationship(
        back_populates="tweet",
        cascade="all, delete-orphan",
        lazy="joined",
        join_depth=2,
    )
    likes: AssociationProxy[List["User"]] = association_proxy(
        "likes_association",
        "user",
    )
    images_association: Mapped[List["TweetsImage"]] = relationship(
        back_populates="tweet",
        cascade="all, delete-orphan",
        lazy="joined",
        join_depth=2,
    )
    attachments: AssociationProxy[List[str]] = association_proxy(
        "images_association",
        "image_path",
    )
    images: AssociationProxy[List["Image"]] = association_proxy(
        "images_association",
        "image",
        creator=lambda x: TweetsImage(image_id=x),
    )

    @classmethod
    def stmt_get_tweets(cls, user: "User"):
        following_id = [following.id for following in user.following]
        following_id.append(user.id)
        return (
            select(Tweet).filter(Tweet.author_id.in_(following_id)).distinct()
        )


class TweetsImage(AsyncAttrs, Base):
    __tablename__ = "tweetsimages"
    id: Mapped[int] = mapped_column(primary_key=True)
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    tweet: Mapped["Tweet"] = relationship(
        back_populates="images_association", lazy="joined", join_depth=2
    )
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    image: Mapped["Image"] = relationship(
        back_populates="tweets_association", lazy="joined", join_depth=2
    )

    @property
    def image_path(self):
        return self.image.path


class User(AsyncAttrs, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    api_key: Mapped[str]
    followers_association: Mapped[List["Follower"]] = relationship(
        back_populates="following",
        foreign_keys="Follower.following_id",
        lazy="joined",
        join_depth=2,
    )
    followers: AssociationProxy[List["User"]] = association_proxy(
        "followers_association",
        "user",
    )
    following_association: Mapped[List["Follower"]] = relationship(
        back_populates="user",
        foreign_keys="Follower.user_id",
        lazy="joined",
        join_depth=2,
    )
    following: AssociationProxy[List["User"]] = association_proxy(
        "following_association",
        "following",
    )
    likes_association: Mapped[List["Like"]] = relationship(
        back_populates="user", lazy="joined", join_depth=2
    )

    @property
    def user_id(self):
        return self.id

    @classmethod
    def stmt_user_by_api_key(cls, api_key):
        return select(User).where(User.api_key == api_key)

    def to_dict(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Follower(AsyncAttrs, Base):
    __tablename__ = "followers"
    __table_args__ = UniqueConstraint(
        "user_id", "following_id"
    ), CheckConstraint("user_id <> following_id")
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    following: Mapped["User"] = relationship(
        back_populates="followers_association",
        foreign_keys="Follower.following_id",
        lazy="joined",
        join_depth=2,
        overlaps="following_association",
    )
    following_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(
        back_populates="following_association",
        foreign_keys="Follower.user_id",
        lazy="joined",
        join_depth=2,
        overlaps="followers_association",
    )

    @classmethod
    def stmt_follower_by_user_following(cls, user_id, following_id):
        return select(Follower).where(
            Follower.following_id == following_id, Follower.user_id == user_id
        )


class Like(AsyncAttrs, Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("tweet_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    tweet: Mapped["Tweet"] = relationship(
        back_populates="likes_association", lazy="joined", join_depth=2
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(
        back_populates="likes_association", lazy="joined", join_depth=2
    )

    @classmethod
    def stmt_like_by_user_tweet(cls, user_id, tweet_id):
        return select(Like).where(
            Like.tweet_id == tweet_id, Like.user_id == user_id
        )
