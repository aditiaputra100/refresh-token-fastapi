from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
import sys

class DatabaseSettings(BaseModel):
    DB_CONNECTION: str = 'sqlite'
    DB_HOST: str | None = None
    DB_PORT: int | None = None
    DB_DATABASE: str | None = 'database.sqlite'
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None



class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    MODE: bool = 'dev' in sys.argv 
    SECRET_KEY: str = 'your_secret_key'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE: DatabaseSettings = DatabaseSettings()


settings = Settings()