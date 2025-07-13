from pydantic_settings import BaseSettings
from pydantic import Field
import streamlit as st
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName, OpenAIModelSettings
import logfire

class AppSettings(BaseSettings):
    """Loads settings from environment variables or a .env file."""
    openai_api_key: str = st.secrets["OPENAI_API_KEY"] | Field(...,validation_alias="OPENAI_API_KEY")
    logfire_key: str = st.secrets["LOGFIRE_KEY"] | Field(...,validation_alias="LOGFIRE_KEY")
    perplexity_api_key: str = st.secrets["PERPLEXITY_API_KEY"] | Field(...,validation_alias="PERPLEXITY_API_KEY")
    # Model Configuration
    research_model_name: OpenAIModelName = "sonar"
    analysis_model_name: OpenAIModelName = "gpt-4.1"
    coupon_model_name: OpenAIModelName = "gpt-4.1"
    chat_model_name: OpenAIModelName = "gpt-4.1-mini"
    
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
perplexity_provider = OpenAIProvider(base_url='https://api.perplexity.ai',api_key=settings.perplexity_api_key)

# Define Models
research_model = OpenAIModel(model_name=settings.research_model_name, provider=perplexity_provider)
analysis_model = OpenAIModel(model_name=settings.analysis_model_name, provider=openai_provider)
coupon_model = OpenAIModel(model_name=settings.coupon_model_name, provider=openai_provider)
chat_model = OpenAIModel(model_name=settings.chat_model_name, provider=openai_provider)