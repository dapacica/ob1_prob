import asyncio
import os
import uuid
from pathlib import Path
from ob1.agent_base import AgentBase
from ob1.utils.logging_utils import log
from anthropic import Anthropic
from ob1.agents.utils.agent_utils import DEFAULT_CODING_AGENT_SYSTEM_PROMPT


class ClaudeAgent(AgentBase):
    """Agent wrapper around Anthropic Claude (Haiku model for speed and cost efficiency)."""

    def __init__(self, name: str):
        super().__init__(name)
        self.client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.model = "claude-3-haiku-20240307"  # cheapest Claude model
        self.run_id = str(uuid.uuid4())[:8]  # short unique ID for logging

    async def run(self, worktree_path: Path, prompt: str):
        """Local mode: generate full code using Claude and write it."""
        code = await self.generate_code_response(prompt)
        (worktree_path / "generated_code.txt").write_text(code)
        await asyncio.sleep(0.5)

    async def generate_files(self, prompt: str) -> dict[str, str]:
        """Remote mode: return Claude-generated code as a file dict."""
        code = await self.generate_code_response(prompt)
        await asyncio.sleep(0.5)
        return {"generated_code.txt": code}

    async def generate_code_response(
        self, prompt: str, system_prompt: str | None = DEFAULT_CODING_AGENT_SYSTEM_PROMPT
    ) -> str:
        """Ask Claude to produce the complete code for the given task.
        Allows overriding the default system prompt."""
        log(f"[ClaudeAgent:{self.run_id}] Generating code for: '{prompt}'")

        user_prompt = f"Task: {prompt}"

        def _sync_call():
            return self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.4,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

        try:
            response = await asyncio.to_thread(_sync_call)
        except Exception as e:
            log(f"[ClaudeAgent:{self.run_id}] Error generating code: {e}")
            return f"# ClaudeAgent:{self.run_id}: generation failed due to error: {e}"

        content = ""
        if response and hasattr(response, "content") and response.content:
            parts = [c.text for c in response.content if hasattr(c, "text")]
            content = "\n".join(parts).strip()

        if content:
            log(f"[ClaudeAgent:{self.run_id}] Code generation completed successfully.")
        else:
            log(f"[ClaudeAgent:{self.run_id}] No content returned from Claude.")

        return content or f"# ClaudeAgent:{self.run_id}: No code generated."
