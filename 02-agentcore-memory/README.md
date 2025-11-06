# Amazon Bedrock AgentCore Memory Lab

Add intelligent memory capabilities to AI agents with Amazon Bedrock AgentCore Memory.

## What is AgentCore Memory?

Amazon Bedrock AgentCore Memory is a fully managed service that gives your AI agents the ability to remember past interactions, enabling them to provide more intelligent, context-aware, and personalized conversations.

### AgentCore Services

- **AgentCore Runtime** ⭐ - Serverless execution with auto-scaling and session management
- **AgentCore Identity** - Secure credential management for API keys and tokens  
- **AgentCore Memory** ⭐ - State persistence and conversation history
- **AgentCore Code Interpreter** - Secure code execution sandbox
- **AgentCore Browser** - Cloud browser automation
- **AgentCore Gateway** - Connects agent to tools and data
- **AgentCore Observability** - Monitoring, tracing, and debugging

## This Lab: AgentCore Memory

This project demonstrates **AgentCore Memory** with two types of memory:

### Short-term Memory
Captures turn-by-turn interactions within a single session. Agents maintain immediate context without requiring users to repeat information.

### Long-term Memory
Automatically extracts and stores key insights from conversations across multiple sessions, including user preferences, important facts, and session summaries.

## Quick Start

### Prerequisites

- [AWS Account](https://aws.amazon.com/account/) with [appropriate permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)
- Python 3.10+ installed
- [AWS CLI configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Basic understanding of [AI agents](https://aws.amazon.com/what-is/ai-agents/) and [AWS services](https://aws.amazon.com/what-is-aws/)

1. **Navigate to Lab02 directory**
```bash
cd 02-agentcore-memory
```

2. **Create deployment folder**
```bash
mkdir deployment
cd deployment
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Deploy to production**
```bash
agentcore configure -e my_agent_memory.py
# Select 'yes' for memory
# Select 'yes' for long-term memory extraction

# Launch to production
agentcore launch
```

3. **Test memory functionality**

Use the `agentcore invoke` CLI command to test memory capabilities. The CLI supports `--session-id` and `--user-id` flags for testing different memory scenarios.

- **Test short-term memory (within session)**

```bash
# Store information in a session
agentcore invoke --session-id session1-alice-memory-test-12345678 --user-id alice '{"prompt": "My name is Alice and I love pizza"}'

# Recall information in the same session
agentcore invoke --session-id session1-alice-memory-test-12345678 --user-id alice '{"prompt": "What is my name and what do I love?"}'
```

- **Test long-term memory (across sessions)**

```bash
# Store preferences in session 1
agentcore invoke --session-id session1-alice-memory-test-12345678 --user-id alice '{"prompt": "I prefer vegetarian food and work as a teacher"}'

# Wait a moment for long-term memory extraction, then test recall in different session
agentcore invoke --session-id session2-alice-memory-test-87654321 --user-id alice '{"prompt": "What do you know about my food preferences and job?"}'
```

Each command uses different session IDs to simulate different conversations, while the same user ID enables cross-session memory.

>The tests use the AWS SDK to call `bedrock-agentcore:InvokeAgentRuntime`, requiring your agent ARN and appropriate permissions. 

## Memory Configuration

The agent uses [AgentCore Memory SDK](https://github.com/aws/bedrock-agentcore-sdk-python/tree/main/src/bedrock_agentcore/memory) for integration with Strands Agents.

### Automatic Memory Setup

When you run `agentcore configure` and enable memory, the AgentCore CLI automatically creates the memory resource (if needed) and sets the `BEDROCK_AGENTCORE_MEMORY_ID` environment variable during `agentcore launch`. Your agent code reads this variable automatically - no manual configuration needed.

### Basic Memory Setup
```python
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig

# Create memory client
client = MemoryClient(region_name="us-west-2") #your region

# Create memory store
basic_memory = client.create_memory(
    name="BasicTestMemory",
    description="Basic memory for testing short-term functionality"
)

# Configure memory with retrieval settings
memory_config = AgentCoreMemoryConfig(
    memory_id=basic_memory.get('id'),
    session_id=session_id,
    actor_id=actor_id,
    retrieval_config={
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
        f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5)
    }
)
```

### Memory Integration with Strands Agents
```python
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Create agent with memory
agent = Agent(
    session_manager=AgentCoreMemorySessionManager(memory_config, REGION),
    system_prompt="You are a helpful assistant with memory. Remember user preferences and facts across conversations."
)
```

## The invoke Function

The `invoke` function is the main entry point for your AgentCore agent. It:

- Receives user prompts and context from AgentCore Runtime
- Extracts session and actor IDs for memory management
- Creates or retrieves the agent instance with memory configuration
- Processes the user message and returns the response

```python
@app.entrypoint
def invoke(payload, context):
    """AgentCore Runtime entry point with lazy-loaded agent"""
    # Extract user prompt
    prompt = payload.get("prompt", "Hello!")
    
    # Get session/actor info for memory
    actor_id = context.request_headers.get('X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id', 'user')
    session_id = context.session_id
    
    # Get agent with memory
    agent = get_or_create_agent(actor_id, session_id)
    
    # Process and return response
    result = agent(prompt)
    return {"response": result.message}
```

## Step 8: Test Memory with Python Applications (Optional)

For more comprehensive testing, you can use the provided test applications that demonstrate both short-term and long-term memory capabilities.

### Test Short-term Memory

Use the `test_short_memory.py` application to test memory within the same session:

```bash
# Set your agent ARN (get from agentcore status)
export AGENT_ARN="YOUR-ARN"

# Run the short-term memory test
python test_short_memory.py
```

This script will test:
- Information storage within a session
- Memory recall in the same session
- Session-based context retention

### Test Long-term Memory

Use the `test_long_memory.py` application to test memory persistence across different sessions:

```bash
# Set your agent ARN (get from agentcore status)
export AGENT_ARN="YOUR-ARN"

# Run the long-term memory test
python test_long_memory.py
```

This script will test:
- Information storage in one session
- Memory extraction and persistence
- Cross-session memory recall
- User-specific memory isolation

**Key Points for Memory Testing:**
- **Agent ARN**: Get this from `agentcore status` output
- **Session IDs**: Must be 33+ characters for proper session management
- **User IDs**: Enable user-specific memory isolation
- **Wait Time**: Allow time between sessions for long-term memory extraction

## Clean Up

```bash
agentcore destroy
```

## Resources

### Documentation
- [What is Amazon Bedrock AgentCore?](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [AgentCore Memory SDK](https://github.com/aws/bedrock-agentcore-sdk-python/tree/main/src/bedrock_agentcore/memory)
- [AgentCore Memory Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Programmatic Agent Invocation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html#invoke-programmatically)

### Code Examples
- [AWS Labs AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples/)