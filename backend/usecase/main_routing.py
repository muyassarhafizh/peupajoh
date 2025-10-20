from enum import Enum
from agents.base import BaseAgent
from usecase.main_workflow import MainWorkflow


class MainRouteEnum(str, Enum):
    ONLY_CHAT = "only_chat"
    FOOD_ANALYSIS = "food_analysis"


class MainRouting:
    def __init__(self, main_routing_agent: BaseAgent, main_workflow: MainWorkflow):
        self.main_routing_agent = main_routing_agent
        self.main_workflow = main_workflow

    def process_user_input(self, user_message: str, session_id: str):
        try:
            output = self.main_routing_agent.run(
                user_message,
                output_schema=MainRouteEnum,
            )

            if output == MainRouteEnum.FOOD_ANALYSIS:
                return self.main_workflow.process_user_input(user_message, session_id)
            else:
                # TODO: Handle only chat
                return {"error": "Only chat is not implemented yet"}
        except Exception as e:
            return {"error": str(e)}
