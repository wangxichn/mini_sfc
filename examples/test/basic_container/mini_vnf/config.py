
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    VNF_SERVER_NAME: str = 'Default'
    VNF_SERVER_TYPE: str = 'Default'
    VNF_SERVER_CPU: str = '1'
    VNF_SERVER_RAM: str = '0.1'
    VNF_SERVER_ROM: str = '1'

config = Config()
