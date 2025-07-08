from pydantic_settings import BaseSettings
from pydantic import Field
from openai import AsyncOpenAI
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName, OpenAIModelSettings
import logfire

class AppSettings(BaseSettings):
    """Loads settings from environment variables or a .env file."""
    logfire_key: str = Field(..., env="LOGFIRE_KEY")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")

    # Model Configuration
    analysis_model_name: OpenAIModelName = "gpt-4-turbo"
    coupon_model_name: OpenAIModelName = "gpt-4-turbo"
    model_temperature: float = 0.1
    model_top_p: float = 0.95

    class Config:
        env_file = ".env"
        extra = "ignore"

# --- Initialize Global Objects ---
settings = AppSettings()

# Configure logging
logfire.configure(token=settings.logfire_key)

# Define shared model settings
default_model_settings = OpenAIModelSettings(
    temperature=settings.model_temperature,
    top_p=settings.model_top_p
)

# Define providers
openai_provider = OpenAIProvider(api_key=settings.openai_api_key)