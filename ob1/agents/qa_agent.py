import os
import subprocess
import time
from pathlib import Path
from ob1.agents.claude_agent import ClaudeAgent
from playwright.sync_api import sync_playwright
from ob1.utils.logging_utils import log
from ob1.agents.utils.agent_utils import DEFAULT_QA_AGENT_SYSTEM_PROMPT


class QATestingAgent:
    """QA Testing Agent that reviews frontend PRs, builds the app, and records a demo video."""

    def __init__(
        self,
        output_dir: Path | str = ".",
        system_prompt: str | None = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.qa_log_path = self.output_dir / "qa_agent_log.txt"
        self.video_path = self.output_dir / "frontend_demo.mp4"
        self.agent = ClaudeAgent("claude")

        self.system_prompt = system_prompt 

    def analyze_code(self, prompt: str, system_prompt: str | None = DEFAULT_QA_AGENT_SYSTEM_PROMPT) -> str:
        """Ask Claude to analyze and verify the code from the PR."""
        effective_prompt = system_prompt or self.system_prompt
        code_analysis = self.agent.generate_code_response(
            prompt,
            system_prompt=effective_prompt,
        )
        self.qa_log_path.write_text(str(code_analysis))
        return code_analysis

    def build_frontend(self):
        """Install dependencies and build the frontend."""
        subprocess.run(["npm", "install"], check=True)
        subprocess.run(["npm", "run", "build"], check=True)

    def start_frontend(self):
        """Start the frontend application."""
        subprocess.Popen(["npm", "start"])
        time.sleep(3)  # wait for local server to start up

    def record_demo(self, url: str = "http://localhost:3000"):
        """Record a short demo video of the running app using Playwright."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(record_video_dir=str(self.output_dir))
            page = context.new_page()
            page.goto(url)
            time.sleep(5)
            context.close()
            browser.close()
        log(f"Video recorded to {self.video_path}")

    def run_full_qa_process(self, prompt: str, system_prompt: str | None = DEFAULT_QA_AGENT_SYSTEM_PROMPT):
        """Run the full QA flow: analyze -> build -> run -> record."""
        log("[QA Agent] Starting automated QA process...")
        self.analyze_code(prompt, system_prompt)
        self.build_frontend()
        self.start_frontend()
        self.record_demo()
        log("[QA Agent] QA process completed successfully.")
