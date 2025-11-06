import asyncio
import os
import json
import subprocess
from pathlib import Path
from ob1.agent_base import AgentBase


'''
NOTE: This agent is failing at the moment due to issues with the Cursor Cloud API creds.
'''

class CursorAgent(AgentBase):
    def __init__(self, name: str):
        super().__init__(name)
        self.api_key = os.getenv("CURSOR_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing CURSOR_API_KEY in environment")
        # Official Cursor API endpoint
        self.api_url = os.getenv("CURSOR_API_URL", "https://api.cursor.com/v0/agents")

    async def run(self, worktree_path: Path, prompt: str):
        code = await self.generate_code_response(prompt)
        (worktree_path / "generated_code.txt").write_text(code)
        await asyncio.sleep(0.5)

    async def generate_files(self, prompt: str) -> dict[str, str]:
        code = await self.generate_code_response(prompt)
        await asyncio.sleep(0.5)
        return {"generated_code.txt": code}

    import asyncio
import os
import json
import subprocess
from pathlib import Path
from ob1.agent_base import AgentBase


class CursorAgent(AgentBase):
    def __init__(self, name: str):
        super().__init__(name)
        self.api_key = os.getenv("CURSOR_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing CURSOR_API_KEY in environment")
        self.api_url = os.getenv("CURSOR_API_URL", "https://api.cursor.com/v0/agents")

    async def run(self, worktree_path: Path, prompt: str):
        """Local mode: launch a Cursor agent via POST and log the response."""
        code = await self.generate_code_response(prompt)
        (worktree_path / "cursor_output.json").write_text(code)
        await asyncio.sleep(0.5)

    async def generate_files(self, prompt: str) -> dict[str, str]:
        """Remote mode: return Cursor API JSON response as file dict."""
        code = await self.generate_code_response(prompt)
        await asyncio.sleep(0.5)
        return {"cursor_output.json": code}

    async def generate_code_response(self, prompt: str) -> str:
        """Launch a Cursor agent for a given prompt/task."""
        repo_url = os.getenv("CURSOR_REPO_URL", "https://github.com/dapacica/ai-pr-orchestrator-demo")
        branch_name = f"feature/{prompt.lower().replace(' ', '-')[:40]}"

        payload = {
            "prompt": {
                "text": prompt,
            },
            "source": {
                "repository": repo_url,
                "ref": "main",
            },
            "target": {
                "autoCreatePr": True,
                "branchName": branch_name,
            },
        }

        curl_cmd = [
            "curl",
            "--fail",
            "--request", "POST",
            "--url", self.api_url,
            "-u", f"{self.api_key}:",
            "--header", "Content-Type: application/json",
            "--data", json.dumps(payload),
        ]

        def _run_curl():
            try:
                result = subprocess.run(
                    curl_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return f"# CursorAgent: curl failed\n{e.stderr or e.stdout}"
        __import__('ipdb').set_trace()
        output = await asyncio.to_thread(_run_curl)

        # Pretty-print JSON if possible
        try:
            data = json.loads(output)
            return json.dumps(data, indent=2)
        except json.JSONDecodeError:
            return output or "# CursorAgent: No output returned"

