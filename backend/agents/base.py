from typing import Optional, List, Any
from enum import Enum
from agno.db.sqlite import SqliteDb


class Framework(str, Enum):
    AGNO = "agno"
    LANGGRAPH = "langgraph"


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"


class AgentConfig:
    """Simple configuration class for your agents"""

    def __init__(
        self,
        name: str,
        model_id: str = "claude-3-5-haiku-latest",
        system_prompt: Optional[str] = None,
        db_file: str = "agno.db",
        temperature: float = 0.7,
        debug_mode: bool = False,
        tools: Optional[List] = None,
        framework: Framework = Framework.AGNO,
        llm_provider: LLMProvider = LLMProvider.ANTHROPIC,
    ):
        self.name = name

        # Convert string to LLMProvider enum if needed
        if isinstance(llm_provider, str):
            try:
                self.llm_provider = LLMProvider(llm_provider.lower())
            except ValueError:
                valid_providers = [p.value for p in LLMProvider]
                raise ValueError(
                    f"Invalid llm_provider: '{llm_provider}'. "
                    f"Must be one of {valid_providers}"
                )
        else:
            self.llm_provider = llm_provider

        # Convert string to Framework enum if needed
        if isinstance(framework, str):
            try:
                self.framework = Framework(framework.lower())
            except ValueError:
                valid_frameworks = [f.value for f in Framework]
                raise ValueError(
                    f"Invalid framework: '{framework}'. "
                    f"Must be one of {valid_frameworks}"
                )
        else:
            self.framework = framework

        self.model_id = model_id
        self.system_prompt = system_prompt
        self.db_file = db_file
        self.temperature = temperature
        self.debug_mode = debug_mode
        self.tools = tools or []


class BaseAgent:
    def __init__(self, config: AgentConfig):
        self.config = config

    def run(
        self,
        input: str,
        input_schema: Optional[Any] = None,
        output_schema: Optional[Any] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> Any:
        if self.config.framework == Framework.AGNO:
            from agno.agent import Agent

            if self.config.llm_provider == LLMProvider.ANTHROPIC:
                from agno.models.anthropic import Claude

                agent = Agent(
                    name=self.config.name,
                    model=Claude(id=self.config.model_id),
                    db=SqliteDb(db_file=self.config.db_file),
                    debug_mode=self.config.debug_mode,
                    add_history_to_context=True,
                    markdown=True,
                    session_state=None,
                    tools=self.config.tools,
                    output_schema=output_schema,
                    input_schema=input_schema,
                )

                if self.config.system_prompt:
                    agent.description = self.config.system_prompt
                return agent.run(input, session_id=session_id, **kwargs)
            elif self.config.llm_provider == LLMProvider.OPENAI:
                from agno.models.openai import OpenAI

                agent = Agent(
                    name=self.config.name,
                    model=OpenAI(id=self.config.model_id),
                    db=SqliteDb(db_file=self.config.db_file),
                    debug_mode=self.config.debug_mode,
                    add_history_to_context=True,
                    markdown=True,
                    session_state=None,
                    tools=self.config.tools,
                    output_schema=output_schema,
                    input_schema=input_schema,
                )

                if self.config.system_prompt:
                    agent.description = self.config.system_prompt
                return agent.run(input, session_id=session_id, **kwargs)
            return []
