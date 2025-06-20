from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key : str = Field(..., validation_alias="OPENAI_API_KEY")
    azure_openai_key : str = Field(..., validation_alias="AZURE_OPENAI_KEY")
    azure_openai_endpoint : str = Field(..., validation_alias="AZURE_OPENAI_ENDPOINT"),
    logfire_key : str = Field(..., validation_alias="LOGFIRE_KEY")

    class Config:
        env_file = ".env"

settings = Settings()

if __name__ == "__main__":
    print(settings.openai_api_key)