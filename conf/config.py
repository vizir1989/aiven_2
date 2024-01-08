from pydantic_settings import BaseSettings


class CommonSettings(BaseSettings):
    DB_DSN: str
    DB_TIMEOUT: int = 5
    MIN_PERIOD: int = 5
    MAX_PERIOD: int = 300


settings = CommonSettings()
