
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    UE_SERVER_NAME: str = 'Default'
    UE_SERVER_TYPE: str = 'Default'

config = Config()
