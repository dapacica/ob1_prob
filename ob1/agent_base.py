from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type


class AgentBase(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, worktree_path: Path, prompt: str):
        """Generate code locally inside worktree_path."""
        pass

    async def generate_files(self, prompt: str) -> dict[str, str]:
        """
        Remote mode: return a mapping of {path: content}.
        Agents that only support local mode can override this.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate_files() for remote mode."
        )


def get_agent_class(name: str) -> Type[AgentBase]:
    from ob1.agents.dummy_agent import DummyAgent
    from ob1.agents.claude_agent import ClaudeAgent
    from ob1.agents.codex_agent import CodexAgent
    # from ob1.agents.cursor_agent import CursorAgent  # temporarily disabled

    lookup = {
        "dummy": DummyAgent,
        "claude": ClaudeAgent,
        "codex": CodexAgent,
        # "cursor": CursorAgent,
    }

    name_lower = name.lower()
    if name_lower == "cursor":
        raise KeyError("CursorAgent is currently unavailable (API restricted). Please use Claude or Codex instead.")
    if name_lower not in lookup:
        raise KeyError(f"Unknown agent '{name}'")

    return lookup[name_lower]

