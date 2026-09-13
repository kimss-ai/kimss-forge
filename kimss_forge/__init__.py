"""kimss_forge — Kimss Forge open-source agent harness (MIT).

Run agents against any OpenAI-compatible endpoint with zero Kimss account.
Connect the Kimss AI Gateway with one line when you need production governance.
"""

from .agent import Agent, AgentResult
from .gateway import KIMSS_GATEWAY_BASE_URL, gateway_headers
from .tools import Tool, tool

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "AgentResult",
    "Tool",
    "tool",
    "gateway_headers",
    "KIMSS_GATEWAY_BASE_URL",
    "__version__",
]
