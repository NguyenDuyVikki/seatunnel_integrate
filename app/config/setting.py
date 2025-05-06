# app/config/setting.py
from pydantic_settings import BaseSettings

# http://172.16.0.2:8080/
class Settings(BaseSettings):
    API_URL: str = "http://127.0.0.1:8080/"
    API_KEY: str = ""
    TIMEOUT: int = 30

    class Config:
        env_prefix = "SEATUNNEL_"



settings = Settings()
