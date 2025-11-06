import argparse
import asyncio
import random
from ob1.orchestrator import run_orchestration

AVAILABLE_AGENTS = ["claude", "codex", "cursor"]

def main():
    parser = argparse.ArgumentParser(description="Run multiple AI agents in parallel.")
    parser.add_argument("-m", "--message", required=True, help="Prompt/task for agents")
    parser.add_argument("-k", "--num_agents", type=int, default=1, help="Number of agents (k)")
    parser.add_argument(
        "--agents",
        default=AVAILABLE_AGENTS,
        nargs="+",
        choices=AVAILABLE_AGENTS,
        help=f"Subset of agents to use (available: {', '.join(AVAILABLE_AGENTS)})",
    )
    parser.add_argument("--remote", action="store_true", help="Use GitHub API (no local clone)")
    parser.add_argument("--test", action="store_true", help="Use dummy agent for testing (ignores others)")
    parser.add_argument("--repo", help="GitHub repo name (e.g. ai-pr-orchestrator-demo)")
    parser.add_argument("--owner", help="GitHub repo owner (default: GH_OWNER env)")

    args = parser.parse_args()

    # Select agents based on flags
    if args.test:
        selected_agents = ["dummy"] * args.num_agents
    else:
        available = args.agents or AVAILABLE_AGENTS
        selected_agents = random.choices(available, k=args.num_agents)
    __import__('ipdb').set_trace()
    asyncio.run(
    run_orchestration(
            args.message,
            selected_agents,
            remote=args.remote,
            owner=args.owner,
            repo=args.repo,
        )
    )

if __name__ == "__main__":
    main()
