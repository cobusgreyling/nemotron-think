"""
nemotron-think: Visible Reasoning Agent Framework for NVIDIA Nemotron models.

See README for usage. The star of the show is VisibleReasoningAgent.
"""

from .agent import VisibleReasoningAgent, AgentRun, AgentStep
from .tools import Tool, DEFAULT_TOOLS
from .helpers import ReasoningTrace

__version__ = "0.1.0"
__all__ = [
    "VisibleReasoningAgent",
    "AgentRun",
    "AgentStep",
    "Tool",
    "DEFAULT_TOOLS",
    "ReasoningTrace",
]
