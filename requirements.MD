You are an AI system designer. I want you to analyze my application requirements and produce a complete system plan.

## 1. Context
We have an existing internal portal where users can type natural language commands. We want to integrate an AI-driven multi-agent system that can perform DevOps and Azure automation tasks.

## 2. Goal of the System
Analyze the proposed strategies and if posible come up with any other alternative proposal.

## Proposed strategies

### Tools
example tools:
 - query the resource groups
 - query virtual machines
 - query each virtual machine and its up time.
 - clean up certain storage blob to certain limit

### Single Agent
single agent with multiple tools. Each tool does some specific things. Single agent understands the intent and runs the multiple tools to do the job and gets a report

### Manager Agent and multiple sub agents
Each agent for each tool and a manager agent understands the intent and assigns the task to specific agent.

## Produce 
- Pros and Cons of each strategy
- Recommended strategy


