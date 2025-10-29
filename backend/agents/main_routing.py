from agents.base import AgentConfig, BaseAgent
from config.settings import settings

NUTRITION_ROUTING_AGENT = AgentConfig(
    name="Nutrition Routing Agent",
    system_prompt="""
    """,  # TODO: Add system prompt
    model_id=settings.model_id,
    temperature=0.3,
    framework=settings.framework_enum,
    llm_provider=settings.llm_provider_enum,
    tools=[],
    debug_mode=True,
)

NutritionRoutingAgent = BaseAgent(NUTRITION_ROUTING_AGENT)
