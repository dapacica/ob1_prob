# test_pr.py
import asyncio
from ob1.orchestrator import run_orchestration

async def main():
    prompt = "Test PR: basic connectivity check"
    await run_orchestration(prompt, k=1, agent_names=["dummy"], remote=True)

if __name__ == "__main__":
    asyncio.run(main())
