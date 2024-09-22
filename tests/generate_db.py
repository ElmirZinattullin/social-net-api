import sys
import os
import pathlib

import dotenv

sys.path.insert(0, os.path.relpath("."))

db_settings = dotenv.dotenv_values(".env")
DATABASE_USER = db_settings.get("DATABASE_USER")
DATABASE_PASSWORD = db_settings.get("DATABASE_PASSWORD")
DATABASE_PORT = 5432
DATABASE = db_settings.get("DATABASE")


if __name__ == "__main__":
    import random, string

    from factories import (
        TweetFactory,
        UserFactory,
    )
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.src.db.models import Follower, Like, Tweet, User

    engine = create_engine(
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@"
        f"localhost:{DATABASE_PORT}/{DATABASE}"
    )
    session = sessionmaker(bind=engine, expire_on_commit=False)


    def get_new_user():
        return UserFactory.simple_generate(create=False)


    def get_new_tweet():
        return TweetFactory.simple_generate(create=False)


    def randomword(length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))



    with session.begin() as s:
        # user generate
        users = []
        for i in range(5):
            new_user: User = get_new_user()
            new_user.api_key = randomword(10)
            users.append(new_user)
            s.add(new_user)
        s.flush()
        users_id = [user.id for user in users]

        # tweet generate
        tweets = []
        for user in users:
            for _ in range(3):
                new_tweet: Tweet = get_new_tweet()
                new_tweet.author = user
                tweets.append(new_tweet)
        # print(len(tweets))
        for i_tweet in range(len(tweets)):
            s.add(tweets[i_tweet * 7 % len(tweets)])
            # print(i_tweet*7 % len(tweets))
        s.flush()

        # like generate
        tweets_ids = [tweet.id for tweet in tweets]
        likes = []
        for user in users:
            k = random.randint(3, 10)
            users_likes = random.sample(tweets_ids, k=k)
            for tweet_id in users_likes:
                new_like = Like(user_id=user.id, tweet_id=tweet_id)
                # print(user.id, )
                likes.append(new_like)
        s.add_all(likes)
        s.flush()

        # following generate
        tweets_ids = [tweet.id for tweet in tweets]
        followers = []
        for user in users:
            k = random.randint(0, 4)
            users_following = random.sample(users_id, k=k)
            for user_id in users_following:
                if user_id != user.id:
                    new_following = Follower(
                        user_id=user.id, following_id=user_id
                    )
                # print(user.id, )
                    followers.append(new_following)
        s.add_all(followers)
        s.flush()

        test_user = s.scalar(select(User).filter(User.api_key == "test"))

        if not test_user:
            new_user: User = User(name="TEST_USER", api_key="test")
            users.append(new_user)
            s.add(new_user)

        print("Users api-keys:")
        api_keys = s.scalars(select(User.api_key))
        for api_key in api_keys:
            print(api_key, end="; ")
        print()
        s.commit()