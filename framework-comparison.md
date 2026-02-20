# Framework Comparison: Autogen vs LangGraph for Multi-Agent Architecture

**Decision Context:** Strategy 3 - Manager Agent + Multiple Sub-Agents for Azure DevOps Automation  
**Date:** February 18, 2026

---

## Executive Summary

For your Azure DevOps automation system with manager+sub-agent architecture:

**Recommendation: Autogen**

**Key Reasons:**
- Native multi-agent orchestration (designed for this pattern)
- Built-in conversation management between agents
- Simpler learning curve for manager-worker patterns
- Better Azure OpenAI integration
- Mature group chat and sequential chat patterns
- Less boilerplate code for agent-to-agent communication

**When to consider LangGraph:**
- Need extremely complex state management
- Require fine-grained control over execution flow
- Want to visualize and debug state transitions
- Need to implement custom routing logic with conditions

---

## Detailed Comparison

### 1. Architecture Alignment

#### Autogen ⭐⭐⭐⭐⭐

**Built for Multi-Agent Systems:**

```python
# Autogen - Natural manager+sub-agent pattern
from autogen import AssistantAgent, GroupChat, GroupChatManager

# Define specialized agents
manager = AssistantAgent(
    name="manager",
    system_message="Coordinate between Azure, Build, and File agents",
    llm_config=llm_config
)

azure_agent = AssistantAgent(
    name="azure_agent",
    system_message="Handle Azure resource operations",
    llm_config=llm_config
)

build_agent = AssistantAgent(
    name="build_agent", 
    system_message="Handle Azure DevOps build operations",
    llm_config=llm_config
)

# Orchestration - Autogen handles agent-to-agent communication
groupchat = GroupChat(
    agents=[manager, azure_agent, build_agent],
    messages=[],
    max_round=10,
    speaker_selection_method="auto"  # or custom function
)

chat_manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Execute
user_proxy.initiate_chat(
    chat_manager,
    message="Show me VMs with high CPU and their failed builds"
)
```

**Pros:**
- GroupChat pattern is perfect for manager delegating to sub-agents
- Built-in speaker selection (manager can choose which agent responds)
- Automatic conversation history management
- Agents can communicate naturally through chat
- Less code needed for orchestration

**Cons:**
- Less control over exact execution flow
- State management is implicit (in conversation history)

---

#### LangGraph ⭐⭐⭐⭐

**Graph-Based Orchestration:**

```python
# LangGraph - More explicit state management
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Define shared state
class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    task: str
    azure_results: dict
    build_results: dict
    final_response: str

# Define nodes (each agent is a node)
def manager_node(state: AgentState):
    # Manager analyzes task and decides routing
    task = state["task"]
    # Call LLM to determine which agents to invoke
    return {"messages": [manager_response]}

def azure_agent_node(state: AgentState):
    # Execute Azure operations
    results = query_azure_resources()
    return {"azure_results": results}

def build_agent_node(state: AgentState):
    # Execute build operations
    results = query_builds()
    return {"build_results": results}

def aggregator_node(state: AgentState):
    # Manager aggregates results
    final = combine_results(state["azure_results"], state["build_results"])
    return {"final_response": final}

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("manager", manager_node)
workflow.add_node("azure_agent", azure_agent_node)
workflow.add_node("build_agent", build_agent_node)
workflow.add_node("aggregator", aggregator_node)

# Define edges (routing logic)
workflow.add_edge("manager", "azure_agent")
workflow.add_edge("manager", "build_agent")
workflow.add_edge("azure_agent", "aggregator")
workflow.add_edge("build_agent", "aggregator")
workflow.add_edge("aggregator", END)

workflow.set_entry_point("manager")

# Compile and execute
app = workflow.compile()
result = app.invoke({"task": "Show me VMs with high CPU and failed builds"})
```

**Pros:**
- Explicit state management (great for debugging)
- Clear visualization of agent flow
- Fine-grained control over routing and conditions
- Can implement complex branching logic
- Better for deterministic workflows

**Cons:**
- More boilerplate code
- Requires explicit state definition
- Less natural for conversational multi-agent interactions
- Need to manually manage agent-to-agent data passing

---

### 2. Development Experience

| Aspect | Autogen | LangGraph |
|--------|---------|-----------|
| **Learning Curve** | Easier - conversational paradigm | Steeper - graph/state concepts |
| **Code Volume** | Less code for common patterns | More boilerplate |
| **Flexibility** | High (conversation-based) | Very High (graph-based) |
| **Debugging** | Conversation logs | State visualization + logs |
| **IDE Support** | Good (typed, documented) | Good (typed, documented) |
| **Documentation** | Excellent with examples | Good but newer |
| **Community** | Large, mature | Growing rapidly |

---

### 3. Azure OpenAI Integration

#### Autogen ⭐⭐⭐⭐⭐

**Native Azure OpenAI Support:**

```python
# Autogen - Direct Azure OpenAI configuration
llm_config = {
    "model": "gpt-4",
    "api_type": "azure",
    "api_key": os.getenv("AZURE_OPENAI_KEY"),
    "api_base": "https://your-resource.openai.azure.com/",
    "api_version": "2024-02-01"
}

agent = AssistantAgent(
    name="agent",
    llm_config=llm_config
)
```

**Pros:**
- Built-in Azure OpenAI support
- Easy configuration
- Handles authentication and retries

---

#### LangGraph ⭐⭐⭐⭐

**Uses LangChain's Azure Integration:**

```python
# LangGraph - Via LangChain
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(
    azure_deployment="gpt-4",
    api_version="2024-02-01",
    azure_endpoint="https://your-resource.openai.azure.com/",
    api_key=os.getenv("AZURE_OPENAI_KEY")
)

# Use in nodes
def agent_node(state):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
```

**Pros:**
- Leverages LangChain's mature Azure integration
- Access to full LangChain ecosystem

**Note:** Both work well with Azure OpenAI, Autogen is slightly simpler

---

### 4. Multi-Agent Patterns

#### Autogen ⭐⭐⭐⭐⭐

**Built-in Patterns:**

1. **GroupChat** (Manager + Sub-Agents):
```python
# Manager automatically routes to appropriate agent
groupchat = GroupChat(agents=[manager, agent1, agent2, agent3])
```

2. **Sequential Chat** (Chain of agents):
```python
# Agent1 → Agent2 → Agent3
user_proxy.initiate_chats([
    {"recipient": agent1, "message": "Step 1"},
    {"recipient": agent2, "message": "Step 2"},
    {"recipient": agent3, "message": "Step 3"}
])
```

3. **Nested Chats** (Hierarchical agents):
```python
# Manager can spawn sub-conversations
agent.register_nested_chats(...)
```

**Perfect for your use case:**
- Manager agent routes to Azure/Build/File agents
- Agents can talk to each other naturally
- Built-in conversation management

---

#### LangGraph ⭐⭐⭐⭐

**Custom Patterns via Graphs:**

```python
# Need to explicitly define routing
def router(state):
    if "azure" in state["task"]:
        return "azure_agent"
    elif "build" in state["task"]:
        return "build_agent"
    else:
        return "file_agent"

workflow.add_conditional_edges(
    "manager",
    router,
    {
        "azure_agent": "azure_agent",
        "build_agent": "build_agent",
        "file_agent": "file_agent"
    }
)
```

**Pros:**
- Complete control over routing logic
- Can implement complex decision trees
- Great for deterministic workflows

**Cons:**
- Requires explicit routing implementation
- More code for simple delegation

---

### 5. Tool Integration

#### Autogen ⭐⭐⭐⭐⭐

**Function Calling Integration:**

```python
# Define tools
def query_azure_vms(resource_group: str) -> dict:
    """Query virtual machines in a resource group"""
    # Implementation
    return {"vms": [...]}

# Register with agent
azure_agent = AssistantAgent(
    name="azure_agent",
    llm_config={
        **llm_config,
        "functions": [
            {
                "name": "query_azure_vms",
                "description": "Query VMs in resource group",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_group": {"type": "string"}
                    }
                }
            }
        ]
    }
)

# Register function execution
azure_agent.register_function(
    function_map={"query_azure_vms": query_azure_vms}
)
```

**Pros:**
- Clean function calling API
- Automatic tool selection by agent
- Built-in execution handling

---

#### LangGraph ⭐⭐⭐⭐

**Tool Integration via LangChain:**

```python
from langchain.tools import tool

@tool
def query_azure_vms(resource_group: str) -> dict:
    """Query virtual machines in a resource group"""
    return {"vms": [...]}

# Use in agent nodes
def azure_agent_node(state):
    # Need to implement tool calling logic
    tools = [query_azure_vms]
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state["messages"])
    
    # Handle tool calls
    if response.tool_calls:
        tool_results = execute_tools(response.tool_calls)
        return {"messages": [tool_results]}
    
    return {"messages": [response]}
```

**Pros:**
- Full LangChain tool ecosystem
- Flexible tool execution

**Cons:**
- More manual tool execution handling

---

### 6. Error Handling and Retries

#### Autogen ⭐⭐⭐⭐⭐

**Built-in Retry Logic:**

```python
llm_config = {
    "model": "gpt-4",
    "retry_wait_time": 10,
    "retry_max_attemps": 5,
    "timeout": 120
}

# Human-in-the-loop for failures
user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="NEVER",  # or "TERMINATE" for confirmation
    max_consecutive_auto_reply=10
)
```

**Features:**
- Automatic retry with exponential backoff
- Human-in-the-loop capability
- Graceful failure handling

---

#### LangGraph ⭐⭐⭐

**Manual Error Handling:**

```python
def agent_node_with_retry(state: AgentState):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = call_llm(state)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                return {"error": str(e)}
            time.sleep(2 ** attempt)  # Exponential backoff
```

**Pros:**
- Full control over error handling
- Can implement custom retry logic

**Cons:**
- Must implement retry logic yourself

---

### 7. State Management

#### Autogen ⭐⭐⭐

**Implicit State (Conversation History):**

```python
# State is maintained in message history
groupchat = GroupChat(
    agents=[manager, azure_agent, build_agent],
    messages=[],  # Conversation history
    max_round=10
)

# Access history
chat_history = groupchat.messages
```

**Pros:**
- Simple - no explicit state management
- Natural for conversational flows

**Cons:**
- Limited structured state
- Harder to track specific data across agents

---

#### LangGraph ⭐⭐⭐⭐⭐

**Explicit State Management:**

```python
class AgentState(TypedDict):
    messages: list
    user_request: str
    azure_vms: list
    build_failures: list
    correlation_results: dict
    final_report: str
    metadata: dict

# State is explicitly passed and updated
def azure_agent(state: AgentState):
    vms = query_vms()
    return {
        "azure_vms": vms,
        "metadata": {"timestamp": datetime.now()}
    }
```

**Pros:**
- Explicit state makes debugging easier
- Type-safe state management
- Can checkpoint and resume
- Perfect for complex data flows

**Cons:**
- More verbose
- Need to define state schema upfront

---

### 8. Monitoring and Observability

#### Autogen ⭐⭐⭐⭐

**Built-in Logging:**

```python
import logging
logging.basicConfig(level=logging.INFO)

# Autogen logs all agent interactions
# Output shows:
# - Which agent is speaking
# - Message content
# - Function calls
# - Results
```

**Integration with Azure:**

```python
from applicationinsights import TelemetryClient
tc = TelemetryClient('instrumentation-key')

# Wrap agent calls
def monitored_chat(message):
    tc.track_event("agent_request", {"message": message})
    result = agent.chat(message)
    tc.track_event("agent_response", {"result": result})
    return result
```

---

#### LangGraph ⭐⭐⭐⭐⭐

**Rich Tracing:**

```python
# LangGraph has excellent tracing via LangSmith
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-key"

# Automatic tracing of:
# - State transitions
# - Node executions
# - LLM calls
# - Tool usage

# Can also export traces
app = workflow.compile()
graph_viz = app.get_graph().draw_mermaid()  # Visualize execution
```

**Pros:**
- LangSmith integration for production monitoring
- State visualization
- Detailed execution traces

---

### 9. Production Deployment

#### Autogen ⭐⭐⭐⭐

**Deployment Options:**

```python
# FastAPI wrapper
from fastapi import FastAPI
app = FastAPI()

@app.post("/chat")
async def chat_endpoint(message: str):
    result = user_proxy.initiate_chat(chat_manager, message=message)
    return {"response": result}

# Azure Container Apps / AKS
# Docker + requirements: autogen[azure]
```

**Considerations:**
- Stateful (conversation history)
- Need session management
- Azure Container Apps works well

---

#### LangGraph ⭐⭐⭐⭐⭐

**Production Features:**

```python
# Checkpointing for long-running tasks
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver

memory = AsyncSqliteSaver.from_conn_string("checkpoints.db")
app = workflow.compile(checkpointer=memory)

# Resume from checkpoint
result = app.invoke(
    {"task": "long task"},
    config={"configurable": {"thread_id": "user123"}}
)

# API deployment
@app.post("/execute")
async def execute_workflow(task: str, user_id: str):
    result = await app.ainvoke(
        {"task": task},
        config={"configurable": {"thread_id": user_id}}
    )
    return result
```

**Pros:**
- Built-in checkpointing
- Resume long-running tasks
- Better for async operations
- Horizontal scaling easier

---

### 10. Cost Comparison

#### Token Usage (1000 requests/day)

**Autogen:**
- Manager routes: 1 LLM call (500 tokens)
- Sub-agent executes: 1 LLM call (1500 tokens)
- Sub-agent responds: 1 LLM call (1000 tokens)
- Total: ~3 LLM calls, 3000 tokens per request
- **Monthly cost: ~$270**

**LangGraph:**
- Similar token usage
- Can optimize with caching and conditional nodes
- **Monthly cost: ~$250-270**

**Verdict:** Similar costs, LangGraph can be optimized more

---

## Decision Matrix

| Criteria | Weight | Autogen | LangGraph | Winner |
|----------|--------|---------|-----------|--------|
| Multi-agent orchestration | 25% | 10 | 8 | Autogen |
| Learning curve | 15% | 9 | 6 | Autogen |
| Azure integration | 10% | 10 | 9 | Autogen |
| State management | 10% | 7 | 10 | LangGraph |
| Production readiness | 15% | 8 | 9 | LangGraph |
| Debugging tools | 10% | 7 | 9 | LangGraph |
| Tool integration | 10% | 10 | 8 | Autogen |
| Community/docs | 5% | 9 | 8 | Autogen |
| **TOTAL SCORE** | | **8.85** | **8.30** | **Autogen** |

---

## Recommendation: Autogen

### Why Autogen for Your Use Case

**1. Natural Manager+Sub-Agent Pattern:**
- Autogen's GroupChat is designed exactly for your architecture
- Manager can naturally delegate to Azure/Build/File agents
- Less boilerplate code

**2. Faster Development:**
- Start building in days, not weeks
- Less code to maintain
- Built-in patterns for common scenarios

**3. Better for Conversational AI:**
- Your portal accepts natural language
- Autogen handles multi-turn conversations natively
- Easier to maintain context

**4. Simpler Azure Integration:**
- Native Azure OpenAI support
- Less configuration needed

**5. Proven for Multi-Agent Systems:**
- Used in production by Microsoft teams
- Strong community examples for similar use cases

### Sample Architecture with Autogen

```python
# autogen_manager_system.py
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import os

# Azure OpenAI configuration
llm_config = {
    "model": "gpt-4",
    "api_type": "azure",
    "api_key": os.getenv("AZURE_OPENAI_KEY"),
    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_version": "2024-02-01",
    "timeout": 120,
    "retry_wait_time": 10
}

# Manager Agent
manager = AssistantAgent(
    name="manager",
    system_message="""You are the Manager Agent coordinating DevOps automation.
    
    Available specialized agents:
    - azure_agent: Azure resources (VMs, storage, resource groups)
    - build_agent: Azure DevOps (pipelines, builds, releases)
    - file_agent: Local file operations
    
    Analyze user requests and delegate to appropriate agents.
    Collect results and provide summary to user.""",
    llm_config=llm_config
)

# Azure Resource Agent
azure_agent = AssistantAgent(
    name="azure_agent",
    system_message="""You are the Azure Resource Agent.
    
    You manage Azure infrastructure:
    - Query resource groups, VMs, storage accounts
    - Check VM status, metrics, uptime
    - Cleanup operations for storage blobs
    
    Use available tools to complete tasks and report results.""",
    llm_config=llm_config
)

# Build Monitoring Agent
build_agent = AssistantAgent(
    name="build_agent",
    system_message="""You are the Build Monitoring Agent.
    
    You handle Azure DevOps operations:
    - Query pipeline status
    - Analyze build failures
    - Check release status
    - Retrieve build logs
    
    Use available tools and report findings.""",
    llm_config=llm_config
)

# File System Agent
file_agent = AssistantAgent(
    name="file_agent",
    system_message="""You are the File System Agent.
    
    You handle local file operations:
    - List files and directories
    - Read file contents
    - Write/update files
    - Delete files with confirmation
    
    Always confirm destructive operations.""",
    llm_config=llm_config
)

# User Proxy (represents portal)
user_proxy = UserProxyAgent(
    name="portal",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0,
    code_execution_config=False
)

# Group Chat setup
groupchat = GroupChat(
    agents=[manager, azure_agent, build_agent, file_agent, user_proxy],
    messages=[],
    max_round=20,
    speaker_selection_method="auto"
)

chat_manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Execution function
def execute_task(user_message: str):
    """Execute user task through multi-agent system"""
    result = user_proxy.initiate_chat(
        chat_manager,
        message=user_message
    )
    return result

# Example usage
if __name__ == "__main__":
    # Test case
    response = execute_task(
        "Show me all VMs in production resource group with high CPU usage"
    )
    print(response)
```

---

## When to Use LangGraph Instead

Consider LangGraph if you need:

1. **Complex State Management:**
   - Tracking many intermediate results
   - Need to access specific data from previous steps
   - Complex data transformations between agents

2. **Deterministic Workflows:**
   - Exact execution order matters
   - Conditional branching based on specific conditions
   - Need to visualize workflow for compliance

3. **Long-Running Tasks:**
   - Workflows that take hours
   - Need checkpointing and resume capability
   - Batch processing scenarios

4. **Custom Routing Logic:**
   - Complex decision trees for agent selection
   - Business rules for delegation
   - Priority-based routing

**Example LangGraph Use Case:**
```
"Clean up all unused resources older than 30 days"
→ This requires:
   1. Query all resource types (checkpoint)
   2. Check last usage date for each (checkpoint)
   3. Create deletion plan (checkpoint)
   4. Get approval (human-in-loop)
   5. Execute deletions in batches (checkpoint after each)
   6. Generate report

LangGraph excels here with checkpoints and explicit state.
```

---

## Migration Path

If you start with Autogen and later need LangGraph:

1. **Autogen is simpler to start:** Get MVP running quickly
2. **Monitor complexity:** Track if state management becomes difficult
3. **Gradual migration:** Can run both frameworks side-by-side
4. **Tool reuse:** Your Azure/DevOps tools work with both

**Timeline:**
- Months 1-6: Build with Autogen
- Month 6: Assess if complexity warrants LangGraph
- Months 7-9: Migrate if needed (or stay with Autogen)

---

## Quick Start Guide (Autogen)

### 1. Installation

```bash
pip install pyautogen[azure]
pip install azure-identity azure-mgmt-compute azure-devops
```

### 2. Environment Setup

```bash
# .env file
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PAT=your-pat
```

### 3. First Agent (15 minutes)

```python
from autogen import AssistantAgent, UserProxyAgent

llm_config = {"model": "gpt-4", "api_type": "azure", ...}

agent = AssistantAgent("assistant", llm_config=llm_config)
user = UserProxyAgent("user", human_input_mode="NEVER")

user.initiate_chat(agent, message="List Azure VMs")
```

### 4. Add Tools (30 minutes)

```python
def list_vms(resource_group: str):
    # Azure SDK call
    return vms

agent.register_function(
    function_map={"list_vms": list_vms}
)
```

### 5. Multi-Agent (1 hour)

```python
manager = AssistantAgent("manager", ...)
azure_agent = AssistantAgent("azure_agent", ...)
build_agent = AssistantAgent("build_agent", ...)

groupchat = GroupChat(agents=[manager, azure_agent, build_agent])
chat_manager = GroupChatManager(groupchat=groupchat)
```

**Total time to working prototype: 2-3 hours**

---

## Resources

### Autogen
- Documentation: https://microsoft.github.io/autogen/
- GitHub: https://github.com/microsoft/autogen
- Examples: https://github.com/microsoft/autogen/tree/main/notebook
- Community: Active Discord and GitHub discussions

### LangGraph
- Documentation: https://langchain-ai.github.io/langgraph/
- GitHub: https://github.com/langchain-ai/langgraph
- Examples: https://github.com/langchain-ai/langgraph/tree/main/examples
- LangSmith: Production monitoring and tracing

---

## Conclusion

**For your Azure DevOps automation system with Strategy 3 (Manager+Sub-Agents):**

✅ **Choose Autogen** because:
- Native multi-agent orchestration
- Faster development and deployment
- Simpler codebase to maintain
- Perfect for conversational delegation pattern
- Strong Azure OpenAI integration
- Lower learning curve for your team

You can build a working multi-agent system in **4-6 weeks** with Autogen vs **8-10 weeks** with LangGraph.

Start with Autogen, and if you hit limitations around state management or need checkpointing for long-running tasks, you can evaluate LangGraph later. The tools and business logic you build will transfer easily.

**Next Steps:**
1. Install Autogen
2. Build first agent with Azure VM listing
3. Add manager and specialized agents
4. Integrate with your portal
5. Deploy to Azure Container Apps

Good luck with your implementation!
