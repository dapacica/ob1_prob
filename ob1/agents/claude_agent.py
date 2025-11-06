import asyncio
import os
from pathlib import Path
from ob1.agent_base import AgentBase
from anthropic import Anthropic


class ClaudeAgent(AgentBase):
    def __init__(self, name: str):
        super().__init__(name)
        self.client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        # Cheapest + fastest Claude model
        self.model = "claude-3-haiku-20240307"

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

    async def generate_code_response(self, prompt: str) -> str:
        """Ask Claude to produce the complete code for the given task."""
        system_prompt = (
            "You are an expert software engineer. "
            "Given a user task, output only the complete code implementation "
            "required to fulfill it. Do not include explanations or text outside the code."
        )
        user_prompt = f"Task: {prompt}"

        # Wrap sync SDK call for async
        def _sync_call():
            return self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.4,
                system=system_prompt,  # ✅ system prompt is now a top-level param
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            )
        __import__('ipdb').set_trace()
        response = await asyncio.to_thread(_sync_call)

        # Extract text content safely
        content = ""
        if response and hasattr(response, "content") and response.content:
            parts = [c.text for c in response.content if hasattr(c, "text")]
            content = "\n".join(parts).strip()

        return content or "# ClaudeAgent: No code generated."
