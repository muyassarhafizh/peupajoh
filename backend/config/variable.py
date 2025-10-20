import os
from dotenv import load_dotenv
from typing import Optional
from config.enum.llm_provider import LLMProvider
from config.enum.framework import Framework

# Load environment variables from .env file
load_dotenv()


class ConfigVariable:
    """Configuration class that loads environment variables"""

    def __init__(self):
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError("OPENAI_API_KEY or ANTHROPIC_API_KEY is required")
        
        # Model Configuration
        self.model_id: Optional[str] = os.getenv("MODEL_ID")
        if not self.model_id:
            raise ValueError("MODEL_ID is required")
        
        llm_provider: Optional[str] = os.getenv("LLM_PROVIDER")
        if not llm_provider:
            raise ValueError("LLM_PROVIDER is required")
        self._determine_llm_provider(llm_provider)
        
        # Framework
        framework: Optional[str] = os.getenv("FRAMEWORK")
        if not framework:
            raise ValueError("FRAMEWORK is required")
        self._determine_framework(framework)
        
        # Database
        self.db_path: Optional[str] = os.getenv("DB_PATH")
        if not self.db_path:
            raise ValueError("DB_PATH is required")

    def _determine_llm_provider(self, llm_provider: str):
        if isinstance(llm_provider, str):
            try:
                self.llm_provider = LLMProvider(llm_provider.lower())
            except ValueError:
                valid_providers = [p.value for p in LLMProvider]
                raise ValueError(
                    f"Invalid llm_provider: '{llm_provider}'. "
                    f"Must be one of {valid_providers}"
                )

    def _determine_framework(self, framework: str):
        if isinstance(framework, str):
            try:
                self.framework = Framework(framework.lower())
            except ValueError:
                valid_frameworks = [f.value for f in Framework]
                raise ValueError(
                    f"Invalid framework: '{framework}'. "
                    f"Must be one of {valid_frameworks}"
                )

# Global config instance
config = ConfigVariable()
        