from agents.base import AgentConfig, BaseAgent
from config.variable import config as config_variable

NUTRITION_ROUTING_AGENT = AgentConfig(
    name="Nutrition Routing Agent",
    system_prompt="""
    """,  # TODO: Add system prompt
    model_id=config_variable.model_id,
    temperature=0.3,
    framework=config_variable.framework,
    llm_provider=config_variable.llm_provider,
    tools=[],
    debug_mode=True,
)

NutritionRoutingAgent = BaseAgent(NUTRITION_ROUTING_AGENT)
