from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    SEATUNNEL_API_URL="http://172.16.0.2:8080/"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SeaTunnel Controller API"
    ENVIRONMENT: str = "local"
    SENTRY_DSN: str = ""
    all_cors_origins: list = ["*"]

settings = Settings()