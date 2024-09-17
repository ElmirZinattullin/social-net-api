from pathlib import Path

import factory
import faker
from faker.providers import BaseProvider
from sqlalchemy import NullPool, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.src.db.models import (
    Follower,
    Image,
    Like,
    Tweet,
    TweetsImage,
    User,
)
from tests.config import IMAGE_PATH, TESTS_DB

engine = create_engine(f"sqlite:///{TESTS_DB}", poolclass=NullPool)
session = scoped_session(sessionmaker(bind=engine))
fake = faker.Faker()


class PathImageProvider(BaseProvider):

    def img_path_provider(self) -> str:
        img, file_name = fake_image()
        return write_to_disk(img, file_name)


def fake_image():
    img = fake.image(image_format="jpeg")
    name = fake.name() + ".jpeg"
    return img, name


def write_to_disk(file, file_name, path=IMAGE_PATH) -> str:
    path = Path(path)
    path.mkdir(exist_ok=True, parents=True)
    file_path = path / file_name
    with open(file_path, mode="wb") as f:
        f.write(file)
    return str(file_path)


fake.add_provider(PathImageProvider)


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    api_key = factory.Faker("bothify", text="??###?###")
    name = factory.Faker("name")


class TweetFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Tweet
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    content = factory.Faker("paragraph")
    author = factory.SubFactory(UserFactory)


class LikeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Like
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    tweet = factory.SubFactory(TweetFactory)
    user = factory.SubFactory(UserFactory)


class FollowerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Follower
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    user = factory.SubFactory(UserFactory)
    following = factory.SubFactory(UserFactory)


class ImageFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Image
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    path = fake.img_path_provider()


class TweetsImageFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = TweetsImage
        sqlalchemy_session = session
        sqlalchemy_session_persistence = "commit"

    tweet = factory.SubFactory(TweetFactory)
    image = factory.SubFactory(ImageFactory)


if __name__ == "__main__":
    # user = UserFactory.simple_generate(create=False)
    # following = FollowerFactory.simple_generate(user=user, create=False)
    # pass
    image = ImageFactory()
    im = fake.img_path_provider()
    print(im)
    pass
