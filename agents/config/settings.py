"""
Invoxio Agent — Pydantic Settings
Loads all environment variables with type safety and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = "Invoxio AI Agent"
    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # Google Gemini
    google_gemini_api_key: str = Field(..., alias="GOOGLE_GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")

    # MongoDB
    mongodb_uri: str = Field(default="", alias="MONGODB_URI")

    # LangSmith
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="invoxio-agent", alias="LANGCHAIN_PROJECT")

    # Agent ReAct Loop
    agent_max_iterations: int = Field(default=10, alias="AGENT_MAX_ITERATIONS")
    agent_temperature: float = Field(default=0.0, alias="AGENT_TEMPERATURE")

    class Config:
        env_file = ".env"
        populate_by_name = True
        extra = "ignore"


# Singleton — import this everywhere
settings = Settings()
