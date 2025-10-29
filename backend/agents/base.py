from typing import Any, List, Optional, Union

from agno.db.sqlite import SqliteDb
from agno.models.message import Message
from pydantic import BaseModel
from config.settings import settings
from config.enum.llm_provider import LLMProvider
from config.enum.framework import Framework


class AgentConfig:
    """Simple configuration class for your agents"""

    def __init__(
        self,
        name: str,
        model_id: str = settings.model_id,
        system_prompt: Optional[str] = None,
        db_file: str = settings.db_path,
        temperature: float = 0.7,
        debug_mode: bool = False,
        tools: Optional[List] = None,
        framework: Framework = settings.framework_enum,
        llm_provider: LLMProvider = settings.llm_provider_enum,
    ):
        self.name = name

        self.llm_provider = llm_provider
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

    def _build_agent(
        self,
        input_schema: Optional[Any],
        output_schema: Optional[Any],
    ):
        if self.config.framework != Framework.AGNO:
            raise NotImplementedError(
                f"{self.config.framework.value} framework not supported."
            )

        from agno.agent import Agent

        if self.config.llm_provider == LLMProvider.ANTHROPIC:
            from agno.models.anthropic import Claude

            model = Claude(id=self.config.model_id)
        elif self.config.llm_provider == LLMProvider.OPENAI:
            from agno.models.openai import OpenAIChat

            model = OpenAIChat(id=self.config.model_id)
        else:
            raise NotImplementedError(
                f"{self.config.llm_provider.value} provider not supported."
            )

        agent = Agent(
            name=self.config.name,
            model=model,
            db=SqliteDb(db_file=self.config.db_file),
            debug_mode=self.config.debug_mode,
            add_history_to_context=True,
            markdown=True,
            tools=self.config.tools,
            output_schema=output_schema,
            input_schema=input_schema,
        )
        if self.config.system_prompt:
            agent.description = self.config.system_prompt
        return agent

    def run(
        self,
        input: Union[str, List[Message], BaseModel],
        input_schema: Optional[Any] = None,
        output_schema: Optional[Any] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> Any:
        agent = self._build_agent(input_schema, output_schema)
        return agent.run(input, session_id=session_id, **kwargs)

    async def arun(
        self,
        input: Union[str, List[Message], BaseModel],
        input_schema: Optional[Any] = None,
        output_schema: Optional[Any] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ) -> Any:
        agent = self._build_agent(input_schema, output_schema)
        return await agent.arun(input, session_id=session_id, **kwargs)
