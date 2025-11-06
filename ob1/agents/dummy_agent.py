import asyncio
import uuid
from pathlib import Path
from ob1.agent_base import AgentBase


class DummyAgent(AgentBase):
    def __init__(self, name: str):
        super().__init__(name)
        self.run_id = str(uuid.uuid4())

    async def run(self, worktree_path: Path, prompt: str):
        """Local mode: write a simple HTML login page with UUID."""
        html = self._generate_html(prompt)
        (worktree_path / "login.html").write_text(html)
        await asyncio.sleep(0.5)  # simulate latency

    async def generate_files(self, prompt: str) -> dict[str, str]:
        """Remote mode: return same HTML file as a dict."""
        await asyncio.sleep(0.5)
        return {"login.html": self._generate_html(prompt)}

    def _generate_html(self, prompt: str) -> str:
        return f"""<html>
                <head><title>Login Page</title></head>
                <body>
                  <h1>{prompt}</h1>
                  <p><b>Agent UUID:</b> {self.run_id}</p>
                  <form>
                    <input placeholder="Email"><br>
                    <input placeholder="Password" type="password"><br>
                    <button>Sign in</button>
                  </form>
                </body>
              </html>"""
