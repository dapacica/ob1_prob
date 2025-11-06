import asyncio
import os
import uuid
from pathlib import Path
from ob1.agent_base import AgentBase
from ob1.utils.logging_utils import log
from openai import OpenAI


class CodexAgent(AgentBase):
    def __init__(self, name: str):
        super().__init__(name)
        self.client = OpenAI(api_key=os.getenv("CODEX_API_KEY"))
        self.model = os.getenv("CODEX_MODEL", "gpt-4-turbo")
        # unique ID for this agent instance (shortened for readability)
        self.run_id = str(uuid.uuid4())[:8]

    async def run(self, worktree_path: Path, prompt: str):
        """Local mode: generate code using Codex (OpenAI) and write it."""
        code = await self.generate_code_response(prompt)
        (worktree_path / "generated_code.txt").write_text(code)
        await asyncio.sleep(0.5)

    async def generate_files(self, prompt: str) -> dict[str, str]:
        """Remote mode: return Codex-generated code as a file dict."""
        code = await self.generate_code_response(prompt)
        await asyncio.sleep(0.5)
        return {"generated_code.txt": code}

    async def generate_code_response(self, prompt: str) -> str:
        """Ask Codex (GPT model) to produce complete code for the task."""
        log(f"[CodexAgent:{self.run_id}] Generating code for: '{prompt}'")

        system_prompt = (
            "You are an expert software engineer. "
            "Given a user task, produce only the complete code implementation "
            "required to fulfill it — no explanations, markdown, or extra text."
        )
        user_prompt = f"Task: {prompt}"

        def _sync_call():
            return self.client.chat.completions.create(
                model=self.model,
                temperature=0.4,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

        try:
            response = await asyncio.to_thread(_sync_call)
        except Exception as e:
            log(f"[CodexAgent:{self.run_id}] Error generating code: {e}")
            return f"# CodexAgent:{self.run_id}: generation failed due to error: {e}"

        content = ""
        if response and hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content.strip()

        if content:
            log(f"[CodexAgent:{self.run_id}] Code generation completed successfully.")
        else:
            log(f"[CodexAgent:{self.run_id}] No content returned from Codex.")

        return content or f"# CodexAgent:{self.run_id}: No code generated."
