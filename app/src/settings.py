from pydantic_settings import BaseSettings
from pydantic import Field


class APISettings(BaseSettings):
    database: str
    database_user: str
    database_password: str
    debug: str = "0"
    database_url: str
    api_route: str = ""

Settings = APISettings().model_dump()

DATABASE = Settings.get("database")
DATABASE_USER = Settings.get("database_user")
DATABASE_PASSWORD = Settings.get("database_password")
DEBUG = bool(int(Settings.get("debug")))
DATABASE_URL = Settings.get("database_url")
API_ROUTE = Settings.get("api_route")

