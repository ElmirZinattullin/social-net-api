import pytest
from sqlalchemy import func, select

from app.src.db import models
from tests.factories import (
    FollowerFactory,
    LikeFactory,
    TweetFactory,
    TweetsImageFactory,
    UserFactory,
    fake,
    fake_image,
    session,
)

ALL_GET = [
    "/tweets",
    "/users/me",
    "/users/2",
]

ALL_POST = [
    "/tweets",
    "/medias",
    "/tweets/{id}/likes",
    "/users/{id}/follow",
]

ALL_DELETE = ["/tweets/{id}", "/tweets/{id}/likes", "/users/{id}/follow"]

ALL = (
    [("get", route) for route in ALL_GET]
    + [("post", route) for route in ALL_POST]
    + [("delete", route) for route in ALL_DELETE]
)


@pytest.mark.parametrize("method, route", ALL)
def test_request_without_key(client, method, route) -> None:
    if "{id}" in route:
        route = route.format(id=1)
    resp = client.request(method, url=route)
    assert resp.status_code == 401
    assert "result" in resp.json()
    assert resp.json()["result"] is False


@pytest.mark.parametrize("method, route", ALL)
def test_request_with_wrong_key(client, method, route) -> None:
    resp = client.post("/tweets", headers={"api-key": "wrong_api"})
    assert resp.status_code == 401
    assert "result" in resp.json()
    assert resp.json()["result"] is False


@pytest.mark.parametrize("route", ALL_GET)
def test_get_methods(client, route) -> None:
    resp = client.get(route, headers={"api-key": "test"})
    assert resp.status_code == 200
    assert "result" in resp.json()


def test_post_api_tweets_good_request(client, first_user) -> None:
    content = fake.paragraph()
    resp = client.post(
        "/tweets", headers={"api-key": "test"}, json={"tweet_data": content}
    )
    assert resp.status_code == 201
    id = resp.json().get("tweet_id")
    tweet = session.get(models.Tweet, id)
    assert tweet.content == content
    assert "result" in resp.json()
    assert "tweet_id" in resp.json()
    assert isinstance(resp.json().get("tweet_id"), int)


def test_post_api_tweets_with_media(client, first_user) -> None:
    content = fake.paragraph()
    resp = client.post(
        "/tweets",
        headers={"api-key": "test"},
        json={"tweet_data": content, "tweet_media_ids": [1, 2, 3]},
    )
    assert resp.status_code == 201
    id = resp.json().get("tweet_id")
    tweet = session.get(models.Tweet, id)
    assert tweet.content == content
    assert "result" in resp.json()


def test_post_api_tweets_create_tweet(client, first_user) -> None:
    content = fake.paragraph()
    pre_count = session.scalar(select(func.count(models.Tweet.id)))
    client.post(
        "/tweets", headers={"api-key": "test"}, json={"tweet_data": content}
    )
    post_count = session.scalar(select(func.count(models.Tweet.id)))
    assert pre_count + 1 == post_count


def test_post_api_tweets_without_key(
    client,
) -> None:
    resp = client.post("/tweets")
    assert resp.status_code == 401
    assert "result" in resp.json()


def test_post_api_tweets_with_wrong_key(
    client,
) -> None:
    resp = client.post("/tweets", headers={"api-key": "wrong_api"})
    assert resp.status_code == 401
    assert "result" in resp.json()


def test_post_api_tweets_with_wrong_method(
    client,
) -> None:
    resp = client.put("/tweets", headers={"api-key": "test"})
    assert resp.status_code == 405
    assert "result" in resp.json()


def test_post_api_medias(
    client,
) -> None:
    img = fake_image()
    pre_count = session.scalar(select(func.count(models.Image.id)))
    resp = client.post(
        "/medias",
        headers={"api-key": "test"},
        files={"file": (img[1], img[0], "image/jpeg")},
    )
    post_count = session.scalar(select(func.count(models.Image.id)))
    assert resp.status_code == 201
    assert pre_count + 1 == post_count
    assert "media_id" in resp.json()
    assert isinstance(resp.json().get("media_id"), int)


def test_post_api_medias_file(
    client,
) -> None:
    img = "str"
    resp = client.post(
        "/medias", headers={"api-key": "test"}, files={"file": img}
    )
    assert resp.status_code == 201


def test_get_api_medias(
    client,
) -> None:
    resp = client.get(
        "/medias",
        headers={"api-key": "test"},
    )
    assert resp.status_code == 405


def test_delete_api_tweets_id_not_exist(
    client,
) -> None:
    resp = client.delete(
        "/tweets/{id}".format(id=10),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 404
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_delete_api_tweets_id(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    api_key = tweet.author.api_key
    resp = client.delete(
        "/tweets/{id}".format(id=id),
        headers={"api-key": api_key},
    )
    assert resp.status_code == 200
    assert "result" in resp.json()
    assert resp.json()["result"] is True


def test_delete_api_tweets_id_wrong_author(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    resp = client.delete(
        "/tweets/{id}".format(id=id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 403
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_delete_api_tweets_id_wrong_method(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    resp = client.get(
        "/tweets/{id}".format(id=id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 405
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_post_api_tweets_id_likes_not_exist(
    client,
) -> None:
    resp = client.post(
        "/tweets/{id}/likes".format(id=10),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 404
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_post_api_tweets_id_likes(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    user = UserFactory()
    user_api_key = user.api_key
    resp = client.post(
        "/tweets/{id}/likes".format(id=id),
        headers={"api-key": user_api_key},
    )
    assert resp.status_code == 201
    assert "result" in resp.json()
    assert resp.json()["result"] is True


def test_post_api_tweets_id_likes_create_like(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    user = UserFactory()
    user_api_key = user.api_key
    pre_count = session.scalar(select(func.count(models.Like.id)))
    client.post(
        "/tweets/{id}/likes".format(id=id),
        headers={"api-key": user_api_key},
    )
    post_count = session.scalar(select(func.count(models.Like.id)))
    assert pre_count + 1 == post_count


def test_post_api_tweets_id_likes_wrong_method(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    user = UserFactory()
    user_api_key = user.api_key
    resp = client.get(
        "/tweets/{id}/likes".format(id=id),
        headers={"api-key": user_api_key},
    )
    assert resp.status_code == 405
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_post_api_tweets_id_likes_double_like(
    client,
) -> None:
    like = LikeFactory()
    tweet_id = like.tweet.id
    user = like.user
    user_api_key = user.api_key
    pre_count = session.scalar(select(func.count(models.Like.id)))
    resp = client.post(
        "/tweets/{id}/likes".format(id=tweet_id),
        headers={"api-key": user_api_key},
    )
    post_count = session.scalar(select(func.count(models.Like.id)))
    assert resp.status_code == 400
    assert pre_count == post_count


# delete_like_tweet


def test_delete_api_tweets_id_like_not_exist(
    client,
) -> None:
    resp = client.delete(
        "/tweets/{id}/likes".format(id=10),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 404
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_delete_api_tweets_id_like(
    client,
) -> None:
    like = LikeFactory()
    id = like.tweet.id
    api_key = like.user.api_key
    pre_count = session.scalar(select(func.count(models.Like.id)))
    resp = client.delete(
        "/tweets/{id}/likes".format(id=id),
        headers={"api-key": api_key},
    )
    post_count = session.scalar(select(func.count(models.Like.id)))
    assert resp.status_code == 200
    assert "result" in resp.json()
    assert resp.json()["result"] is True
    assert pre_count == post_count + 1


def test_delete_api_tweets_id_like_wrong_method(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    resp = client.put(
        "/tweets/{id}/likes".format(id=id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 405
    assert "result" in resp.json()
    assert resp.json()["result"] is False


# post /api/users/id/follow
def test_post_api_users_id_follow_not_exist(
    client,
) -> None:
    resp = client.post(
        "/users/{id}/follow".format(id=10),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 404
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_post_api_users_id_follow(
    client,
) -> None:
    user = UserFactory()
    user_api_key = user.api_key
    following = UserFactory()
    following_id = following.id
    resp = client.post(
        "/users/{id}/follow".format(id=following_id),
        headers={"api-key": user_api_key},
    )
    assert resp.status_code == 201
    assert "result" in resp.json()
    assert resp.json()["result"] is True


def test_post_api_users_id_follow_create_record(
    client,
) -> None:
    user = UserFactory()
    user_api_key = user.api_key
    following = UserFactory()
    following_id = following.id
    pre_count = session.scalar(select(func.count(models.Follower.id)))
    client.post(
        "/users/{id}/follow".format(id=following_id),
        headers={"api-key": user_api_key},
    )
    post_count = session.scalar(select(func.count(models.Follower.id)))
    assert pre_count + 1 == post_count


def test_post_api_users_id_follow_wrong_method(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    user = UserFactory()
    user_api_key = user.api_key
    resp = client.get(
        "/users/{id}/follow".format(id=id),
        headers={"api-key": user_api_key},
    )
    assert resp.status_code == 405
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_post_api_users_id_follow_double_following(
    client,
) -> None:
    follower = FollowerFactory()
    user_api_key = follower.user.api_key
    following_id = follower.following_id
    pre_count = session.scalar(select(func.count(models.Follower.id)))
    resp = client.post(
        "/users/{id}/follow".format(id=following_id),
        headers={"api-key": user_api_key},
    )
    post_count = session.scalar(select(func.count(models.Follower.id)))
    assert resp.status_code == 400
    assert pre_count == post_count


def test_post_api_users_id_follow_following_self(
    client,
) -> None:
    user = UserFactory()
    resp = client.post(
        "/users/{id}/follow".format(id=user.id),
        headers={"api-key": user.api_key},
    )
    assert resp.status_code == 400


# delete api/users/id/follow
def test_delete_api_users_id_follow_not_exist(
    client,
) -> None:
    resp = client.delete(
        "/users/{id}/follow".format(id=10),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 404
    assert "result" in resp.json()
    assert resp.json()["result"] is False


def test_delete_api_users_id_follow(
    client,
) -> None:
    follower = FollowerFactory()
    id = follower.following.id
    api_key = follower.user.api_key
    pre_count = session.scalar(select(func.count(models.Follower.id)))
    resp = client.delete(
        "/users/{id}/follow".format(id=id),
        headers={"api-key": api_key},
    )
    post_count = session.scalar(select(func.count(models.Follower.id)))
    assert resp.status_code == 200
    assert "result" in resp.json()
    assert resp.json()["result"] is True
    assert pre_count == post_count + 1


def test_delete_api_users_id_follow_wrong_method(
    client,
) -> None:
    tweet = TweetFactory()
    id = tweet.id
    resp = client.put(
        "/users/{id}/follow".format(id=id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 405
    assert "result" in resp.json()
    assert resp.json()["result"] is False


# get api/users/me
def test_get_users_me_user(
    client,
) -> None:
    user = UserFactory()
    resp = client.get(
        "/users/me",
        headers={"api-key": user.api_key},
    )
    assert resp.status_code == 200
    assert resp.json().get("user") is not None
    assert resp.json().get("user").get("name") == user.name


def test_get_users_me_user_following(
    client,
) -> None:
    user = UserFactory()
    following = UserFactory()
    FollowerFactory(user=user, following=following)
    resp = client.get(
        "/users/me",
        headers={"api-key": user.api_key},
    )
    assert resp.status_code == 200
    assert resp.json().get("user").get("following") is not None
    following_schema = {"id": following.id, "name": following.name}
    assert following_schema in resp.json().get("user").get("following")


def test_get_users_me_user_follower(
    client,
) -> None:
    user = UserFactory()
    follower = UserFactory()
    FollowerFactory(user=follower, following=user)
    resp = client.get(
        "/users/me",
        headers={"api-key": user.api_key},
    )
    assert resp.status_code == 200
    assert resp.json().get("user").get("followers") is not None
    follower_schema = {"id": follower.id, "name": follower.name}
    assert follower_schema in resp.json().get("user").get("followers")


# get api/users/id
def test_get_users_id(
    client,
) -> None:
    user = UserFactory()
    resp = client.get(
        "/users/{id}".format(id=user.id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 200
    assert resp.json().get("user") is not None
    assert resp.json().get("user").get("name") == user.name


def test_get_users_id_following(
    client,
) -> None:
    user = UserFactory()
    following = UserFactory()
    FollowerFactory(user=user, following=following)
    resp = client.get(
        "/users/{id}".format(id=user.id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 200
    assert resp.json().get("user").get("following") is not None
    following_schema = {"id": following.id, "name": following.name}
    assert following_schema in resp.json().get("user").get("following")


def test_get_users_id_follower(
    client,
) -> None:
    user = UserFactory()
    follower = UserFactory()
    FollowerFactory(user=follower, following=user)
    resp = client.get(
        "/users/{id}".format(id=user.id),
        headers={"api-key": "test"},
    )
    assert resp.status_code == 200
    assert resp.json().get("user").get("followers") is not None
    follower_schema = {"id": follower.id, "name": follower.name}
    assert follower_schema in resp.json().get("user").get("followers")


# get api/tweets
def test_get_tweets(
    client,
) -> None:
    TweetFactory()
    resp = client.get(
        "/tweets",
        headers={"api-key": "test"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json().get("tweets"), list)


def test_get_tweets_tweet(
    client,
) -> None:
    like = LikeFactory()
    tweet = like.tweet
    resp = client.get(
        "/tweets",
        headers={"api-key": "test"},
    )
    tweet_schema = {
        "id": tweet.id,
        "content": tweet.content,
        "attachments": [],
        "author": {"id": tweet.author.id, "name": tweet.author.name},
        "likes": [{"user_id": like.user_id, "name": like.user.name}],
    }

    assert tweet_schema in resp.json().get("tweets")


def test_get_tweets_tweet_with_attachemnts(
    client,
) -> None:
    tweet_image = TweetsImageFactory()
    tweet = tweet_image.tweet
    image = tweet_image.image

    resp = client.get(
        "/tweets",
        headers={"api-key": "test"},
    )
    tweet_schema = {
        "id": tweet.id,
        "content": tweet.content,
        "attachments": [image.path],
        "author": {"id": tweet.author.id, "name": tweet.author.name},
        "likes": [],
    }

    assert tweet_schema in resp.json().get("tweets")
