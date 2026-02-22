"""
Two-agent system: Manager + Azure Storage agent.

Flow:
  user_proxy  →  manager  (understands intent, rewrites task)
  user_proxy  →  storage_agent  (calls real Azure tools, returns results)

The manager rewrites the user message into a precise task description, then
user_proxy hands it to storage_agent which calls the registered tools.
"""

import logging
from typing import Annotated, Dict, Any, Optional

from autogen import AssistantAgent, UserProxyAgent, register_function

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.azure_storage import list_blobs, list_containers

logger = logging.getLogger(__name__)

MANAGER_PROMPT = """\
You are a Manager Agent that helps users explore Azure Storage accounts.

Your only job: read the user's request and restate it as a single, precise
instruction for the storage agent, e.g.:
  "List all containers in storage account <name>."
  "List all blobs in container <container> of storage account <name>."

Output ONLY that instruction — no extra text, no TERMINATE.
"""

STORAGE_PROMPT = """\
You are an Azure Storage Agent with two tools:

1. tool_list_containers(account_name) — lists all containers.
2. tool_list_blobs(account_name, container_name, prefix, max_results) — lists blobs.

Steps:
1. Call the appropriate tool with the parameters from the instruction.
2. Report the result exactly as returned by the tool.
3. End your reply with TERMINATE.
"""


# ── Tool wrappers with type annotations ────────────────────────────────

def tool_list_containers(
    account_name: Annotated[str, "Azure storage account name"],
) -> str:
    """List all containers in an Azure storage account."""
    return list_containers(account_name)


def tool_list_blobs(
    account_name: Annotated[str, "Azure storage account name"],
    container_name: Annotated[Optional[str], "Container to list (omit for all)"] = None,
    prefix: Annotated[Optional[str], "Blob name prefix filter"] = None,
    max_results: Annotated[int, "Max blobs to return"] = 50,
) -> str:
    """List blobs in a storage account, optionally filtered by container and prefix."""
    return list_blobs(account_name, container_name, prefix, max_results)


def build_agent_system(llm_config: Dict[str, Any]):
    """
    Return (user_proxy, manager, storage_agent).

    Usage in main.py:
        user_proxy, manager, storage_agent = build_agent_system(llm_config)

        # Step 1: manager rewrites the user request into a precise task
        user_proxy.initiate_chat(manager, message=user_input, max_turns=1)
        task = user_proxy.last_message(manager)["content"]

        # Step 2: storage_agent executes the task with real tools
        user_proxy.initiate_chat(storage_agent, message=task, max_turns=5)
    """

    manager = AssistantAgent(
        name="manager",
        system_message=MANAGER_PROMPT,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    storage_agent = AssistantAgent(
        name="storage_agent",
        system_message=STORAGE_PROMPT,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    # max_consecutive_auto_reply must be > 0 so user_proxy can send
    # the tool result back to storage_agent after execution
    user_proxy = UserProxyAgent(
        name="user",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
        is_termination_msg=lambda m: "TERMINATE" in (m.get("content") or ""),
    )

    register_function(
        tool_list_containers,
        caller=storage_agent,
        executor=user_proxy,
        name="tool_list_containers",
        description="List all containers in an Azure storage account",
    )
    register_function(
        tool_list_blobs,
        caller=storage_agent,
        executor=user_proxy,
        name="tool_list_blobs",
        description="List blobs in a storage account, optionally filtered by container and prefix",
    )

    return user_proxy, manager, storage_agent
