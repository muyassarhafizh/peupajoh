"""Unified configuration settings for Peupajoh backend and API."""

import os
from typing import List, Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.enum.llm_provider import LLMProvider
from config.enum.framework import Framework


class Settings(BaseSettings):
    """
    Unified configuration for both backend (agents/workflow) and FastAPI.

    Loads from environment variables and .env file.
    """

    # ========================================
    # Backend/Agent Configuration
    # ========================================

    # API Keys
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")

    # Model Configuration
    model_id: str = Field(..., description="LLM model identifier")
    llm_provider: str = Field(..., description="LLM provider (anthropic or openai)")
    framework: str = Field(..., description="Agent framework (agno)")

    # Database
    db_path: str = Field(..., description="Path to SQLite database")

    # ========================================
    # FastAPI Configuration
    # ========================================

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Auto-reload on code changes")

    # API Metadata
    api_title: str = Field(default="Peupajoh API", description="API title")
    api_description: str = Field(
        default="Food tracking and nutrition analysis API",
        description="API description"
    )
    api_version: str = Field(default="1.0.0", description="API version")
    api_prefix: str = Field(default="/api/v1", description="API URL prefix")

    # Documentation URLs
    docs_url: str = Field(default="/api/docs", description="Swagger UI URL")
    redoc_url: str = Field(default="/api/redoc", description="ReDoc URL")

    # CORS Settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="CORS allow credentials"
    )
    cors_allow_methods: List[str] = Field(
        default=["*"],
        description="CORS allowed methods"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="CORS allowed headers"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # ========================================
    # Validators
    # ========================================

    @field_validator("llm_provider", mode="before")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        if v is None:
            raise ValueError("LLM_PROVIDER is required")

        try:
            # Validate it's a valid enum value
            LLMProvider(v.lower())
            return v.lower()
        except ValueError:
            valid_providers = [p.value for p in LLMProvider]
            raise ValueError(
                f"Invalid llm_provider: '{v}'. Must be one of {valid_providers}"
            )

    @field_validator("framework", mode="before")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        """Validate framework."""
        if v is None:
            raise ValueError("FRAMEWORK is required")

        try:
            # Validate it's a valid enum value
            Framework(v.lower())
            return v.lower()
        except ValueError:
            valid_frameworks = [f.value for f in Framework]
            raise ValueError(
                f"Invalid framework: '{v}'. Must be one of {valid_frameworks}"
            )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        # Validate at least one API key is provided
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError(
                "Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be provided"
            )

    # ========================================
    # Properties for backward compatibility
    # ========================================

    @property
    def llm_provider_enum(self) -> LLMProvider:
        """Get LLM provider as enum."""
        return LLMProvider(self.llm_provider)

    @property
    def framework_enum(self) -> Framework:
        """Get framework as enum."""
        return Framework(self.framework)


# Global settings instance
settings = Settings()
