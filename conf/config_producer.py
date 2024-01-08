from conf.config import CommonSettings


class Settings(CommonSettings):
    CONCURRENCY: int = 3
    SLEEP_WITHOUT_TASK: int = 1
    SLEEP_AFTER_EXCEPTION: int = 1


settings = Settings()
