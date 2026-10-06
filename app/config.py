from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider: "mock" | "openai" | "azure"
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-06-01"

    database_url: str = "sqlite:///./triage.db"

    # Drop hypotheses below this confidence after guardrail validation.
    min_hypothesis_confidence: float = 0.0

    # Weight of the LLM's self-reported confidence when blending with severity.
    confidence_llm_weight: float = 0.6


@lru_cache
def get_settings() -> Settings:
    return Settings()
