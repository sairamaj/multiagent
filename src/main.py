"""
Main entry point for the Multi-Agent DevOps Automation System

This module provides a command-line interface for interacting with the agent system.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent))

from agents import ManagerAgentSystem
from config_loader import config_loader


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_ENDPOINT"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("Error: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these environment variables and try again.")
        print("\nExample:")
        print("  export AZURE_OPENAI_KEY=your-key")
        print("  export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        return False
    
    return True


def run_interactive_mode(manager_system: ManagerAgentSystem):
    """Run in interactive mode"""
    print("\n" + "=" * 70)
    print("Multi-Agent DevOps Automation System - Interactive Mode")
    print("=" * 70)
    print("\nType your requests in natural language.")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'examples' to see example commands.")
    print("=" * 70 + "\n")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'examples':
                print_examples()
                continue
            
            # Execute task
            print("\nExecuting task...")
            result = manager_system.execute_task(user_input)
            
            if result["success"]:
                print("\n✓ Task completed successfully")
                print(f"\nSummary:")
                print(result["summary"])
            else:
                print("\n✗ Task failed")
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def run_single_command(manager_system: ManagerAgentSystem, command: str):
    """Execute a single command"""
    print(f"\nExecuting: {command}")
    print("-" * 70)
    
    result = manager_system.execute_task(command)
    
    if result["success"]:
        print("\n✓ Task completed successfully\n")
        print("Summary:")
        print(result["summary"])
    else:
        print("\n✗ Task failed\n")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return 0 if result["success"] else 1


def print_examples():
    """Print example commands"""
    print("\nExample Commands:\n")
    
    examples = [
        ("Azure Resources", [
            "List all virtual machines matching the CI template pattern",
            "Show me VMs that would be deleted in cleanup",
            "Check which VMs are non-compliant with naming patterns"
        ]),
        ("Build Monitoring", [
            "Show build failures from the last 7 days",
            "Analyze build failures and identify patterns",
            "Get build metrics and success rate for last week"
        ]),
        ("Storage Cleanup", [
            "Show me what blobs would be cleaned up",
            "Calculate storage usage for CI artifacts",
            "List all blob retention policies"
        ]),
        ("File Operations", [
            "List all Python files in src directory",
            "Show configuration files",
            "Calculate size of config directory"
        ])
    ]
    
    for category, commands in examples:
        print(f"{category}:")
        for cmd in commands:
            print(f"  • {cmd}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent DevOps Automation System"
    )
    parser.add_argument(
        "-c", "--command",
        type=str,
        help="Execute a single command"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start REST API server"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show example commands"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Show examples if requested
    if args.examples:
        print_examples()
        return 0
    
    # Start API if requested
    if args.api:
        logger.info("Starting REST API server...")
        import uvicorn
        from api.app import app
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return 0
    
    # Validate environment
    if not validate_environment():
        return 1
    
    # Configure Azure OpenAI (for pyautogen 0.2.x with OpenAI 1.x+ API)
    llm_config = {
        "config_list": [{
            "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
            "api_type": "azure",
            "api_key": os.getenv("AZURE_OPENAI_KEY"),
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        }],
        "temperature": 0.7
    }
    
    try:
        # Initialize manager system
        logger.info("Initializing multi-agent system...")
        manager_system = ManagerAgentSystem(llm_config)
        logger.info("System initialized successfully")
        
        # Execute command or run interactive mode
        if args.command:
            return run_single_command(manager_system, args.command)
        elif args.interactive:
            run_interactive_mode(manager_system)
            return 0
        else:
            # Default to interactive mode
            run_interactive_mode(manager_system)
            return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
