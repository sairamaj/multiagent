"""
Manager Agent - Orchestrates specialized sub-agents

The manager agent:
1. Understands user intent
2. Breaks down complex tasks
3. Delegates to appropriate sub-agents
4. Collects and synthesizes results
"""

import logging
from typing import Dict, Any, List, Optional
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config_loader import config_loader

logger = logging.getLogger(__name__)


class ManagerAgentSystem:
    """
    Manager Agent System using Autogen's GroupChat pattern.
    
    Coordinates between specialized agents:
    - Azure Resource Agent: VM management, resource queries
    - Build Monitoring Agent: Pipeline status, build failures
    - File System Agent: Local file operations
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize the manager agent system.
        
        Args:
            llm_config: Azure OpenAI configuration
        """
        self.llm_config = llm_config
        self.config_loader = config_loader
        
        # Initialize agents
        self._init_agents()
        
        # Set up group chat
        self._init_group_chat()
        
        logger.info("ManagerAgentSystem initialized")
    
    def _init_agents(self):
        """Initialize all agents in the system"""
        
        # Manager Agent
        self.manager = AssistantAgent(
            name="manager",
            system_message=self._get_manager_system_message(),
            llm_config=self.llm_config,
            human_input_mode="NEVER"
        )
        
        # Azure Resource Agent
        self.azure_agent = AssistantAgent(
            name="azure_agent",
            system_message=self._get_azure_agent_system_message(),
            llm_config=self.llm_config,
            human_input_mode="NEVER"
        )
        
        # Build Monitoring Agent
        self.build_agent = AssistantAgent(
            name="build_agent",
            system_message=self._get_build_agent_system_message(),
            llm_config=self.llm_config,
            human_input_mode="NEVER"
        )
        
        # File System Agent
        self.file_agent = AssistantAgent(
            name="file_agent",
            system_message=self._get_file_agent_system_message(),
            llm_config=self.llm_config,
            human_input_mode="NEVER"
        )
        
        # User Proxy (represents the portal)
        self.user_proxy = UserProxyAgent(
            name="portal",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE")
        )
    
    def _get_manager_system_message(self) -> str:
        """Get system message for manager agent"""
        return """You are the Manager Agent coordinating DevOps automation tasks.

Your responsibilities:
1. Understand user requests and identify the intent
2. Determine which specialized agent(s) should handle the task
3. Break down complex tasks into subtasks
4. Delegate to appropriate agents (azure_agent, build_agent, file_agent)
5. Collect results and synthesize a comprehensive response

Available specialized agents:
- azure_agent: Azure resource management (VMs, storage, resource groups, cleanup operations)
- build_agent: Azure DevOps operations (pipeline status, build failures, deployments)
- file_agent: Local file system operations (read, write, list files)

Decision rules:
- VM queries, resource groups, Azure resources → azure_agent
- Build status, pipeline failures, deployments → build_agent
- File operations, logs → file_agent
- Complex tasks may require multiple agents

When delegating:
1. Be specific about what each agent should do
2. Provide necessary context (VM patterns, retention counts from configuration)
3. Coordinate the sequence if tasks are dependent
4. Summarize results for the user

After all agents complete their tasks, provide a clear summary and end with "TERMINATE".
"""
    
    def _get_azure_agent_system_message(self) -> str:
        """Get system message for Azure agent"""
        
        # Load relevant configuration
        vm_patterns = self.config_loader.get_all_vm_patterns()
        cleanup_config = self.config_loader.get_vm_cleanup_config()
        
        patterns_str = "\n".join([
            f"  - {name}: {pattern.get('pattern', '')}"
            for name, pattern in vm_patterns.items()
        ])
        
        return f"""You are the Azure Resource Agent specialized in Azure infrastructure management.

Your capabilities:
1. Query Azure resources (VMs, storage accounts, resource groups)
2. Manage virtual machines (list, start, stop, delete)
3. Execute cleanup operations based on retention policies
4. Check resource compliance with naming patterns
5. Monitor resource usage and costs

CONFIGURATION (VM Naming Patterns):
{patterns_str}

VM Cleanup Policy:
- Keep latest: {cleanup_config.get('keep_latest_count', 5)} VMs
- Age threshold: {cleanup_config.get('age_threshold_days', 30)} days
- Exclude tags: {', '.join(cleanup_config.get('exclude_tags', []))}

When performing operations:
1. Always check configuration for patterns and policies
2. For cleanup operations, use dry_run=True first unless explicitly told otherwise
3. Verify VM names match expected patterns before operations
4. Report what would be deleted before actual deletion
5. Include counts, names, and dates in your responses

Tools available (pseudo-code, report intent):
- list_vms(resource_group, pattern)
- cleanup_old_vms(pattern_type, dry_run)
- check_vm_compliance(vm_name)
- get_vm_details(vm_name)

Report your findings clearly and ask for confirmation on destructive operations.
When done, state your results and return control to manager.
"""
    
    def _get_build_agent_system_message(self) -> str:
        """Get system message for Build agent"""
        
        # Load relevant configuration
        monitoring_config = self.config_loader.get_pipeline_monitoring_config()
        
        return f"""You are the Build Monitoring Agent specialized in Azure DevOps operations.

Your capabilities:
1. Query pipeline and build status
2. Analyze build failures and identify patterns
3. Monitor deployment status
4. Track build performance metrics
5. Generate build reports

CONFIGURATION (Pipeline Monitoring):
- Check interval: {monitoring_config.get('check_interval_minutes', 5)} minutes
- Alert on failure: {monitoring_config.get('alert_on_failure', True)}

Common failure patterns you should recognize:
- OutOfMemoryError → Memory issues
- Connection timed out → Network issues
- Test failed → Test failures
- npm ERR! → Dependency issues
- docker: Error → Docker issues

When analyzing builds:
1. Identify the failure category
2. Check for known patterns in configuration
3. Suggest remediation steps
4. Report trends if multiple failures

Tools available (pseudo-code, report intent):
- query_pipeline_status(pipeline_name)
- get_build_failures(days)
- analyze_build_logs(build_id)
- get_deployment_status(environment)

Provide actionable insights and clear status reports.
When done, state your results and return control to manager.
"""
    
    def _get_file_agent_system_message(self) -> str:
        """Get system message for File agent"""
        return """You are the File System Agent specialized in local file operations.

Your capabilities:
1. List files and directories
2. Read file contents
3. Write and update files
4. Delete files (with confirmation)
5. Search for files by pattern

Safety rules:
1. NEVER delete files without explicit confirmation
2. Always report what would be deleted first
3. Backup important files before modification
4. Validate file paths before operations
5. Report errors clearly

Tools available (pseudo-code, report intent):
- list_files(directory, pattern)
- read_file(file_path)
- write_file(file_path, content)
- delete_file(file_path, confirm)
- find_files(pattern)

When performing operations:
1. Verify file paths exist
2. Check permissions
3. For destructive operations, ask for confirmation first
4. Report success/failure clearly

Provide clear confirmations and status updates.
When done, state your results and return control to manager.
"""
    
    def _init_group_chat(self):
        """Initialize group chat for agent coordination"""
        
        # Create group chat with all agents
        self.groupchat = GroupChat(
            agents=[
                self.user_proxy,
                self.manager,
                self.azure_agent,
                self.build_agent,
                self.file_agent
            ],
            messages=[],
            max_round=20,
            speaker_selection_method="auto"
        )
        
        # Create chat manager
        self.chat_manager = GroupChatManager(
            groupchat=self.groupchat,
            llm_config=self.llm_config
        )
    
    def execute_task(self, user_message: str) -> Dict[str, Any]:
        """
        Execute a user task through the multi-agent system.
        
        Args:
            user_message: Natural language task description
        
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing task: {user_message}")
        
        try:
            # Clear previous messages
            self.groupchat.messages = []
            
            # Initiate chat
            self.user_proxy.initiate_chat(
                self.chat_manager,
                message=user_message
            )
            
            # Extract results from conversation
            result = {
                "success": True,
                "message": user_message,
                "conversation": self.groupchat.messages,
                "summary": self._extract_summary()
            }
            
            logger.info("Task execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {
                "success": False,
                "message": user_message,
                "error": str(e)
            }
    
    def _extract_summary(self) -> str:
        """Extract summary from conversation messages"""
        if not self.groupchat.messages:
            return "No messages in conversation"
        
        # Get the last few messages for summary
        recent_messages = self.groupchat.messages[-3:]
        
        summary_parts = []
        for msg in recent_messages:
            name = msg.get("name", "unknown")
            content = msg.get("content", "")
            if content and not content.startswith("TERMINATE"):
                summary_parts.append(f"{name}: {content[:200]}...")
        
        return "\n".join(summary_parts) if summary_parts else "Task completed"


# Example usage and testing
if __name__ == "__main__":
    import os
    logging.basicConfig(level=logging.INFO)
    
    # Configure Azure OpenAI
    llm_config = {
        "model": "gpt-4",
        "api_type": "azure",
        "api_key": os.getenv("AZURE_OPENAI_KEY"),
        "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_version": "2024-02-01",
        "temperature": 0.7
    }
    
    # Initialize manager system
    manager_system = ManagerAgentSystem(llm_config)
    
    # Example tasks
    print("\n" + "=" * 70)
    print("MULTI-AGENT SYSTEM - EXAMPLE TASKS")
    print("=" * 70)
    
    # Task 1: List VMs
    print("\n### Task 1: List CI Template VMs ###")
    result1 = manager_system.execute_task(
        "List all virtual machines matching the CI template pattern"
    )
    print(f"Success: {result1['success']}")
    print(f"Summary: {result1['summary']}")
    
    # Task 2: Cleanup VMs
    print("\n### Task 2: Cleanup Old VMs (Dry Run) ###")
    result2 = manager_system.execute_task(
        "Show me what VMs would be deleted if we cleaned up old CI templates"
    )
    print(f"Success: {result2['success']}")
    print(f"Summary: {result2['summary']}")
    
    # Task 3: Check Build Status
    print("\n### Task 3: Check Build Failures ###")
    result3 = manager_system.execute_task(
        "Check for any build failures in the last 7 days and identify common patterns"
    )
    print(f"Success: {result3['success']}")
    print(f"Summary: {result3['summary']}")
