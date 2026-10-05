"""kimss_forge — Kimss Forge open-source agent harness (MIT).

Run agents against any OpenAI-compatible endpoint with zero Kimss account.
Connect the Kimss AI Gateway with one line when you need production governance.
"""

from .agent import Agent, AgentResult
from .gateway import KIMSS_GATEWAY_BASE_URL, gateway_headers
from .run_context import RunContext, ensure_root_context, get_run_context
from .tools import Tool, tool

__version__ = "0.1.1"
__all__ = [
    "Agent",
    "AgentResult",
    "Tool",
    "tool",
    "gateway_headers",
    "KIMSS_GATEWAY_BASE_URL",
    "RunContext",
    "ensure_root_context",
    "get_run_context",
    "__version__",
]
