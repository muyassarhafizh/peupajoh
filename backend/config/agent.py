
class AgentConfig:
    """Simple configuration class for your agents"""

    def __init__(
        self,
        name: str,
        model_id: str = "gpt-4o",
        system_prompt: Optional[str] = None,
        db_file: str = "agno.db",
        temperature: float = 0.7,
        debug_mode: bool = False,
        tools: Optional[List] = None,
        output_schema: Optional[Any] = None,
        input_schema: Optional[Any] = None,
    ):
        self.name = name
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.db_file = db_file
        self.temperature = temperature
        self.debug_mode = debug_mode
        self.tools = tools or []
        self.output_schema = output_schema
        self.input_schema = input_schema


class Agent:
    def __init__(self, agent_config: AgentConfig):
        self.config = agent_config
        self.agent = create_agent(agent_config)

    def run(self, message: str) -> RunOutput:
        pass

