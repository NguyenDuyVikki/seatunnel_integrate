# app/config/setting.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_URL: str = "http://172.16.0.2:8080/"
    API_KEY: str = ""
    TIMEOUT: int = 30

    class Config:
        env_prefix = "SEATUNNEL_"



settings = Settings()
