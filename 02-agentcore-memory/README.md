# Amazon Bedrock AgentCore Memory Lab

Add intelligent memory capabilities to AI agents with Amazon Bedrock AgentCore Memory.

## What is AgentCore Memory?

Amazon Bedrock AgentCore Memory is a fully managed service that gives your AI agents the ability to remember past interactions, enabling them to provide more intelligent, context-aware, and personalized conversations.

### AgentCore Services

- **[AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime.html)** ⭐ - Serverless execution with auto-scaling and session management
- **[AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html)** - Secure credential management for API keys and tokens  
- **[AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)** ⭐ - State persistence and conversation history
- **[AgentCore Code Interpreter](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-interpreter-tool.html)** - Secure code execution sandbox
- **[AgentCore Browser](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-tool.html)** - Cloud browser automation
- **[AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)** - API management and tool discovery
- **[AgentCore Observability](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html)** - Monitoring, tracing, and debugging
- **[AgentCore Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)** - Deterministic control and security boundaries for agent-tool interactions
- **[AgentCore Evaluations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html)** - Automated assessment and performance measurement for agents

## This Lab: AgentCore Memory

This project demonstrates **AgentCore Memory** with two types of memory:

### Short-term Memory
Captures turn-by-turn interactions within a single session. Agents maintain immediate context without requiring users to repeat information.

### Long-term Memory
Automatically extracts and stores key insights from conversations across multiple sessions, including user preferences, important facts, and session summaries.

## Prerequisites

- [AWS Account](https://aws.amazon.com/account/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) with [appropriate permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)
- [AWS CLI configured](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AgentCore CLI](https://github.com/aws/agentcore-cli) installed (`npm install -g @aws/agentcore`, requires Node.js 20.12+) and [uv](https://docs.astral.sh/uv/getting-started/installation/) — see [Lab 01](../01-agentcore-runtime/)
- Python 3.10+ with `boto3` (`pip install boto3`) for the optional test scripts in Step 7
- Basic understanding of [AI agents](https://aws.amazon.com/what-is/ai-agents/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) and [AWS services](https://aws.amazon.com/what-is-aws/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el)

## Step 1: Navigate to Lab Directory

```bash
cd 02-agentcore-memory
```

The agent code lives in [`agent/`](agent/) (`main.py` + `pyproject.toml`).

## Step 2: Create the Project with Memory

Create an AgentCore project and add a Runtime for the agent:

```bash
agentcore create --name MemoryLab --skip-git
cd MemoryLab
agentcore add runtime --name memory_agent --language python \
  --request-header-allowlist X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id
cp ../agent/main.py ../agent/pyproject.toml app/memory_agent/
```

### Custom Header Configuration

`--request-header-allowlist` lets the Runtime receive the `X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id` header. In `agentcore/agentcore.json` the Runtime now has:

```json
"requestHeaderAllowlist": [
  "X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id"
]
```

This header allows passing a user identifier from your application to the agent. The agent extracts it from `context.request_headers` (normalized to lowercase: `x-amzn-bedrock-agentcore-runtime-custom-actor-id`) and uses it to namespace memory per user.

### Add AgentCore Memory

Add a memory with long-term extraction strategies (facts, user preferences, and session summaries):

```bash
agentcore add memory --name LabMemory --strategies SEMANTIC,USER_PREFERENCE,SUMMARIZATION
```

## Step 3: Deploy to Production

```bash
agentcore deploy
```

This creates the AgentCore Memory resource, deploys the agent to AgentCore Runtime, and grants the Runtime's execution role access to the memory.

## Step 4: Test Memory Functionality

Use the `agentcore invoke` CLI command to test memory capabilities. It supports `--session-id` and `--header` flags for testing different memory scenarios.

**Important:** Session IDs must be at least 33 characters long.

### Test Short-term Memory (within session)

Store information in a session:

```bash
agentcore invoke --runtime memory_agent \
  --session-id session1-laura-test-12345678901234 \
  --payload '{"prompt": "My name is Laura and I love banana"}'
```

Recall information in the same session:

```bash
agentcore invoke --runtime memory_agent \
  --session-id session1-laura-test-12345678901234 \
  --payload '{"prompt": "What is my name and what do I love?"}'
```

### Test Long-term Memory (across sessions)

Store preferences in session 1:

```bash
agentcore invoke --runtime memory_agent \
  --session-id session1-user456-test-1234567890123 \
  --header "X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id: user456" \
  --payload '{"prompt": "I prefer vegetarian food and work as a teacher"}'
```

**Important:** Long-term memory extraction is an [asynchronous background process](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-saving-and-retrieving-insights.html#long-term-step-2-retrieve-extracted-insights) that can take a minute or more. Wait at least a few minutes before testing recall in a different session:

```bash
agentcore invoke --runtime memory_agent \
  --session-id session2-user456-test-9876543210987 \
  --header "X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id: user456" \
  --payload '{"prompt": "What do you know about my food preferences and job?"}'
```

**Key Points:**
- Session IDs must be at least 33 characters long
- Short-term memory works within a single session without needing the actor ID header
- Long-term memory requires the custom header to identify users across different sessions
- Long-term memory extraction is an [asynchronous process](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-saving-and-retrieving-insights.html#long-term-step-2-retrieve-extracted-insights) that can take a minute or more
- Same custom header value enables cross-session memory for that user
- Invocations without the header share the `default-user` actor, so facts extracted from other header-less tests (for example, Laura) can show up in their answers

>The CLI calls `bedrock-agentcore:InvokeAgentRuntime` with your AWS credentials.

## Step 5: Understanding Memory Configuration

The agent uses [AgentCore Memory SDK](https://github.com/aws/bedrock-agentcore-sdk-python/tree/main/src/bedrock_agentcore/memory) for integration with Strands Agents.

### Automatic Memory Setup

Every memory you add to the project is passed to the Runtime as environment variables named after it: `MEMORY_<NAME>_ID` and `MEMORY_<NAME>_ARN`. For `LabMemory`, the agent reads `MEMORY_LABMEMORY_ID` - no manual configuration needed.

### Basic Memory Setup
```python
import os
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig

# Injected by the AgentCore CLI for the "LabMemory" memory
MEMORY_ID = os.getenv("MEMORY_LABMEMORY_ID")

# HTTP headers are normalized to lowercase
CUSTOM_HEADER_NAME = 'x-amzn-bedrock-agentcore-runtime-custom-actor-id'

# Configure memory with retrieval settings
memory_config = AgentCoreMemoryConfig(
    memory_id=MEMORY_ID,
    session_id=session_id,
    actor_id=actor_id,
    retrieval_config={
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.2),
        f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.2)
    }
)
```

`relevance_score` is the minimum similarity score a record needs to be retrieved. Natural questions such as "What do you know about my job?" typically score around 0.3–0.4 against stored facts, so a high threshold (for example 0.5) silently filters out valid memories.

The namespaces match the defaults that `agentcore add memory` creates for the `SEMANTIC` (`/users/{actorId}/facts`) and `USER_PREFERENCE` (`/users/{actorId}/preferences`) strategies.

### Memory Integration with Strands Agents
```python
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Create agent with memory
agent = Agent(
    session_manager=AgentCoreMemorySessionManager(memory_config, REGION),
    system_prompt="You are a helpful assistant with memory. Remember user preferences and facts across conversations."
)
```

## Step 6: Understanding the Agent Code

The `invoke` function is the main entry point for your AgentCore agent. It:

- Receives user prompts and context from AgentCore Runtime
- Extracts the custom header for user identification (normalized to lowercase)
- Creates or retrieves the agent instance with memory configuration
- Processes the user message and returns the response

```python
@app.entrypoint
def invoke(payload, context: RequestContext):
    """AgentCore Runtime entry point with lazy-loaded agent"""
    if not MEMORY_ID:
        return {"error": "Memory not configured. Run `agentcore add memory --name LabMemory` and redeploy (sets MEMORY_LABMEMORY_ID)."}

    # Extract custom header and session information
    actor_id = 'default-user'
    if context and context.request_headers:
        # Headers are normalized to lowercase
        actor_id = context.request_headers.get(CUSTOM_HEADER_NAME) or actor_id

    session_id = context.session_id
    app.logger.info("Using actor_id='%s', session_id='%s'", actor_id, session_id)

    # Get or create agent (lazy loading)
    agent = get_or_create_agent(actor_id, session_id)

    prompt = payload.get("prompt", "Hello!")
    result = agent(prompt)

    return {
        "response": result.message.get('content', [{}])[0].get('text', str(result))
    }
```

## Step 7: Test Memory with Python Applications (Optional)

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

**Note:** Long-term memory extraction is an [asynchronous background process](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-saving-and-retrieving-insights.html#long-term-step-2-retrieve-extracted-insights) that can take a minute or more. The test waits 120 seconds between sessions; if the second session does not recall the facts yet, wait a little longer and run it again.

**Key Points for Memory Testing:**
- **Agent ARN**: Get this from `agentcore status` output
- **Session IDs**: Must be 33+ characters for proper session management
- **Custom Headers**: Use boto3 event handlers with `X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id` for user-specific memory
- **Long-term Memory Extraction**: An [asynchronous background process](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-saving-and-retrieving-insights.html#long-term-step-2-retrieve-extracted-insights) that can take a minute or more. For testing, wait a few minutes between storing and retrieving long-term memories

## Step 8: Clean Up

Remove the resources from the project and deploy the empty project to delete the stack (Runtime, Memory, and IAM roles):

```bash
agentcore remove all --yes
agentcore deploy --yes
```

The Runtime's CloudWatch log groups (`/aws/bedrock-agentcore/runtimes/...`) are kept. Delete them from the CloudWatch console if you don't need them.

## Resources

### Documentation
- [What is Amazon Bedrock AgentCore?](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [AgentCore CLI](https://github.com/aws/agentcore-cli)
- [AgentCore Memory SDK](https://github.com/aws/bedrock-agentcore-sdk-python/tree/main/src/bedrock_agentcore/memory)
- [AgentCore Memory Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Invoke an AgentCore Runtime agent](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html)

### Code Examples
- [AWS Labs AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples/)
