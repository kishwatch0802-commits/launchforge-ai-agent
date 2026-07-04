"""ADK-style runtime compatibility layer.

Google ADK encourages modelling work as specialist agents coordinated by a
runner/session layer. This file keeps that shape while remaining dependency
light for the capstone: if `google.adk` exists, the project can be extended to
wrap these classes; otherwise this deterministic runner provides the same
conceptual boundary for tests and the Streamlit demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Protocol


try:  # pragma: no cover - optional dependency is not required for the MVP.
    import google.adk as google_adk  # type: ignore
except Exception:  # noqa: BLE001
    google_adk = None


class RunnableAgent(Protocol):
    name: str
    role: str

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass
class AgentEvent:
    agent: str
    role: str
    summary: str


@dataclass
class AgentSession:
    """Minimal session object mirroring an ADK runner's evolving state."""

    context: Dict[str, Any]
    events: List[AgentEvent] = field(default_factory=list)


class SequentialAgentRunner:
    """Run agents in order and merge each output into a shared context."""

    def __init__(self, agents: Iterable[RunnableAgent]):
        self.agents = list(agents)

    def run(self, initial_context: Dict[str, Any]) -> AgentSession:
        session = AgentSession(context=dict(initial_context))
        for agent in self.agents:
            output = agent.run(session.context)
            session.context.update(output)
            session.events.append(
                AgentEvent(
                    agent=agent.name,
                    role=agent.role,
                    summary=f"{agent.name} produced {', '.join(sorted(output.keys()))}.",
                )
            )
        return session


def adk_available() -> bool:
    return google_adk is not None
