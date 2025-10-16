from enum import Enum


class SessionState(str, Enum):
    """Enumeration of possible session states in the food tracking workflow"""

    INITIAL = "initial"  # First action from user
    CLARIFYING = "clarifying"  # Search food agent responding to user
    ADVISING = "advising"  # Search food agent forwarding to advisor agent
    ADVISED = "advised"  # Advisors sent to user
