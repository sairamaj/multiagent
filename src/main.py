"""
Entry point for the Multi-Agent Azure Storage system.

Usage:
    python src/main.py                                          # interactive
    python src/main.py -c "list blobs in storage account foo"  # single command
    python src/main.py -v                                       # verbose
"""

import os
import sys
import logging
import warnings
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Suppress noisy third-party warnings before any autogen imports
warnings.filterwarnings("ignore", message="flaml.automl is not available.*")
logging.getLogger("autogen.oai.client").setLevel(logging.ERROR)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agents import build_agent_system


def _llm_config():
    key = os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not key or not endpoint:
        print("Error: set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT in .env")
        sys.exit(1)
    return {
        "config_list": [{
            "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
            "api_type": "azure",
            "api_key": key,
            "azure_endpoint": endpoint,
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        }],
        "temperature": 0.3,
    }


def run_task(message: str, llm: dict):
    """
    Two-step execution:
      1. Manager rewrites the user message into a precise task.
      2. Storage agent calls real Azure tools to fulfil the task.
    """
    user_proxy, manager, storage_agent = build_agent_system(llm)

    # Step 1 — manager clarifies / rewrites the task (single turn)
    user_proxy.initiate_chat(manager, message=message, max_turns=1)
    task = user_proxy.last_message(manager)["content"]

    print()  # blank line between the two conversations

    # Step 2 — storage agent executes the task with real tool calls
    user_proxy.initiate_chat(storage_agent, message=task, max_turns=5)


def run_interactive():
    print("=" * 60)
    print("  Multi-Agent Azure Storage Explorer")
    print("=" * 60)
    print("Ask me to list blobs or containers in a storage account.")
    print("Type 'quit' to exit.\n")

    llm = _llm_config()

    while True:
        try:
            msg = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break
        if not msg:
            continue
        if msg.lower() in ("quit", "exit"):
            print("Bye!")
            break

        run_task(msg, llm)
        print()


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Azure Storage Explorer")
    parser.add_argument("-c", "--command", help="Run a single command and exit")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if args.command:
        run_task(args.command, _llm_config())
    else:
        run_interactive()


if __name__ == "__main__":
    main()
