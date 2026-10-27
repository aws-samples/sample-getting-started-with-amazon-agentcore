# Building a Calculator Agent with Amazon Bedrock AgentCore

Deploy production-ready AI agents in minutes with Amazon Bedrock AgentCore Runtime and the [AgentCore CLI](https://github.com/aws/agentcore-cli).

## What is AgentCore?

Amazon Bedrock AgentCore is a suite of services that simplifies deploying AI agents to production. Instead of weeks configuring infrastructure, you get production-ready agents with a few CLI commands.

### AgentCore Services

- **AgentCore Runtime** ⭐ - Serverless execution with auto-scaling and session management
- **AgentCore Identity** - Secure credential management for API keys and tokens  
- **AgentCore Memory** - State persistence and conversation history
- **AgentCore Code Interpreter** - Secure code execution sandbox
- **AgentCore Browser** - Cloud browser automation
- **AgentCore Gateway** - API management and tool discovery
- **AgentCore Observability** - Monitoring, tracing, and debugging

## Calculator Agent with AgentCore Runtime

This project demonstrates **AgentCore Runtime** by building a calculator agent that handles mathematical computations using the Strands Agents framework with automatic scaling and session isolation.

## Key Benefits

- **10 minutes** from code to production endpoint
- **Serverless** - no infrastructure management
- **Auto-scaling** - handles traffic spikes automatically
- **Session-aware** - maintains conversation context across invocations
- **Built-in security** - AWS security best practices included


## Core Components

1. **Amazon Bedrock AgentCore Runtime**: Provides a secure serverless runtime for deploying and scaling dynamic agents using any framework with any model provider.

2. **Strands Agents**: An agent framework that build production-ready, multi-agent AI systems in a few lines of code. 

3. **AgentCore CLI** (`@aws/agentcore`): The recommended tool to create, run locally, deploy, and invoke agents on AgentCore. It deploys your project with AWS CDK.

## Prerequisites

Before you begin, verify that you have:

- **AWS Account** with appropriate permissions
- **AWS CLI configured** with `aws configure`
- **Node.js 20.12+** (for the AgentCore CLI)
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (the CLI uses it to run and package Python agents)
- **AWS Permissions**: Attach the [BedrockAgentCoreFullAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/BedrockAgentCoreFullAccess.html) AWS managed policy. The CLI deploys with AWS CloudFormation (CDK), so your identity also needs permissions to deploy CloudFormation stacks and create IAM roles
- **Model Access**: Anthropic Claude Sonnet (or the model of your preference) [enabled in the Amazon Bedrock console](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

> **New AWS customers receive up to $200 in credits**  
> Get started at no cost with the [AWS Free Tier](https://aws.amazon.com/free/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el).

## Step 1: AWS Account Setup

### Create AWS Account and Configure Permissions

If you're using admin access, you can skip the detailed permissions setup. Otherwise, follow [these steps to create an AWS IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) and attach the [BedrockAgentCoreFullAccess](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/BedrockAgentCoreFullAccess.html) AWS managed policy.

### Configure the AWS CLI

Run the following command in your terminal:

```bash
aws configure
```

Enter your credentials:
- `AWS Access Key ID [None]`: (from your downloaded CSV file)
- `AWS Secret Access Key [None]`: (from your downloaded CSV file)
- `Default region name [None]`:  (your AWS Region)
- `Default output format [None]`: `json`

## Step 2: Install the AgentCore CLI

```bash
npm install -g @aws/agentcore
```

Verify installation:

```bash
agentcore --version
```

> **Upgrading from the Bedrock AgentCore Starter Toolkit?** The Python `bedrock-agentcore-starter-toolkit` is no longer supported. Uninstall it (`pip uninstall bedrock-agentcore-starter-toolkit`) because both tools provide an `agentcore` command.

## Step 3: Review the Agent Code

The agent lives in the [`agent/`](agent/) folder:

```
agent/
├── main.py           # the agent and its AgentCore Runtime entry point
└── pyproject.toml    # dependencies
```

`agent/main.py`:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
import os
from strands_tools import calculator

# System prompt for the agent
SYSTEM_PROMPT = "You are a helpful assistant that can perform calculations. Use the calculate tool for any math problems."

# Model configuration from environment variable (Amazon Bedrock model or inference profile ID)
MODEL_ID = os.getenv("MODEL_ID", "global.anthropic.claude-sonnet-5-5")

# Global agent instance for reuse across invocations
agent = None

# Initialize the Bedrock AgentCore application
app = BedrockAgentCoreApp()

def create_agent(tools):
    """Create agent with lazy loading pattern for performance"""
    global agent
    if agent is None:
        agent = Agent(
            model=MODEL_ID,
            tools=[tools],
            system_prompt=SYSTEM_PROMPT
        )
    return agent

@app.entrypoint
def invoke(payload):
    """AgentCore Runtime entry point"""
    agent = create_agent(calculator)
    prompt = payload.get("prompt", "Hello!")
    result = agent(prompt)

    return {
        "response": result.message.get('content', [{}])[0].get('text', str(result))
    }

if __name__ == "__main__":
    app.run()
```

`agent/pyproject.toml` declares the dependencies. The AgentCore CLI reads them from `[project].dependencies` (it does not use `requirements.txt`):

```toml
dependencies = [
    "aws-opentelemetry-distro >= 0.21.0",
    "bedrock-agentcore >= 1.18.1, < 2.0.0",
    "strands-agents >= 1.62.0, < 2.0.0",
    "strands-agents-tools >= 0.8.10, < 1.0.0",
]
```

**Required packages:**
- `bedrock-agentcore` - Amazon Bedrock AgentCore SDK (implements the Runtime contract)
- `aws-opentelemetry-distro` - required by AgentCore Runtime; also sends traces and logs to CloudWatch
- `strands-agents` - Strands Agents SDK
- `strands-agents-tools` - Tools for Strands Agents including calculator functionality

## Step 4: Understanding the Calculator Agent Code

The agent implements several key components:

### AgentCore Runtime Entry Point

The `@app.entrypoint` decorator makes your agent deployable to AgentCore Runtime. This is the only difference between a local script and a cloud-deployed agent.

### Agent Initialization with Lazy Loading

The agent is initialized once per session to preserve state and avoid performance costs. Amazon Bedrock AgentCore Runtime provides dedicated microVMs with up to 8 hours lifetime or 15 minutes of inactivity timeout.

### Calculator Tool

The agent includes a calculator tool from `strands-tools` for performing mathematical operations.

## Step 5: Create the AgentCore Project

From this lab folder (`01-agentcore-runtime/`), create a project and add a Runtime for the agent:

```bash
agentcore create --name CalculatorLab --skip-git
cd CalculatorLab
agentcore add runtime --name calculator --language python
```

`agentcore add runtime` registers the Runtime in `agentcore/agentcore.json` and creates the `app/calculator/` folder. Copy the agent code into it:

```bash
cp ../agent/main.py ../agent/pyproject.toml app/calculator/
```

Your project now looks like this:

```
CalculatorLab/
├── agentcore/
│   ├── agentcore.json     # project spec: Runtimes, Memory, Gateways...
│   ├── aws-targets.json   # deployment targets (account + region)
│   └── cdk/               # AWS CDK app that deploys the project
└── app/
    └── calculator/
        ├── main.py
        └── pyproject.toml
```

## Step 6: Test Locally 

Start the local development server (it installs the dependencies with uv and reloads when you save):

```bash
agentcore dev
```

The server starts on `http://localhost:8080`. Keep this terminal open - the server needs to stay running for testing.

**Test the calculator agent** (open a new terminal, inside `CalculatorLab/`):

```bash
agentcore invoke --local --runtime calculator --payload '{"prompt": "What is 25 * 4?"}'
```

You can also call the local endpoint directly with curl:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Calculate 15 + 27"
  }'
```

**To stop the server:** Press `Ctrl+C` in the terminal running `agentcore dev`.

## Step 7: Deploy to AgentCore Runtime

```bash
agentcore deploy
```

On the first deploy the CLI creates the `default` target from your AWS account and Region. This command:
- Packages your code and dependencies with uv (direct code deploy, no Docker required)
- Creates an IAM execution role with the permissions the Runtime needs
- Deploys your agent to Amazon Bedrock AgentCore Runtime with an AWS CloudFormation stack (AWS CDK)
- Configures CloudWatch logging

### Check Deployment Status

```bash
agentcore status
```

Note the Runtime ARN from the output - you'll need it for programmatic invocation.

### Find Your Resources

After deployment, view your resources in the AWS Console:

| Resource | Location |
|----------|----------|
| Agent Logs | CloudWatch → Log groups → `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` (or run `agentcore logs runtime --name calculator`) |
| Deployment Stack | CloudFormation → Stacks |
| IAM Role | IAM → Roles → Search for the stack name |

## Step 8: Test Your Deployed Agent

### Simple Invocation

Session IDs must be at least 33 characters long. Use the same session ID to keep the conversation context:

```bash
agentcore invoke --runtime calculator \
  --session-id calculator-session-test-1234567890123 \
  --payload '{"prompt": "What is 50 plus 30?"}'
```

### Test Conversation Memory

Test that the agent maintains context within a session:

```bash
agentcore invoke --runtime calculator \
  --session-id calculator-session-test-1234567890123 \
  --payload '{"prompt": "Now multiply that result by 2"}'
```

> AgentCore Runtime routes requests with the same session ID to the same isolated session, so the agent keeps its conversation context.

## Step 9: Invoke from Production Applications

For production applications, use the [InvokeAgentRuntime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html) operation from [AWS SDK](https://aws.amazon.com/what-is/sdk/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el). 

```python
    # Invoke the agent
    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_arn,
        runtimeSessionId=session_id, #Must be 33+ characters
        payload=payload,
        qualifier="DEFAULT"
    )
```

Use [invoke_agent.py](invoke_agent.py) application to test the agent, or the [test_agentcore.ipynb](test_agentcore.ipynb) notebook.

Run the script to test both calculation capabilities and memory:

```bash
# Set your agent ARN (get from agentcore status)
export AGENT_ARN="YOUR-ARN"

# Run the test script
python invoke_agent.py
```

The script will test:
- Basic calculations
- Memory persistence within a session
- Mathematical operations
- Conversation context retention

**Key Points for Production Use:**
- **Agent ARN**: Get this from `agentcore status` output
- **Session IDs**: Must be 33+ characters for session persistence
- **Authentication**: Uses your AWS credentials (IAM roles, access keys, etc.)


For more troubleshooting information, see [Troubleshoot Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/troubleshoot-runtime.html).

## Step 10: Automated Deployment (Optional)

For automation scenarios like CI/CD pipelines, every AgentCore CLI command runs non-interactively with flags, and `--json` returns machine-readable output:

```bash
agentcore deploy --json
agentcore status --json
```

Because the project is an AWS CDK app (`agentcore/cdk/`), you can also extend `agentcore/cdk/lib/cdk-stack.ts` to add your own AWS resources and grant your agent access to them. See [Extending the CDK app](https://github.com/aws/agentcore-cli#extending-the-cdk-app).

## Step 11: Using the Anthropic API (optional)

The [`agent_anthropic/`](agent_anthropic/) folder contains an agent that calls the Anthropic API directly with the [Strands Agents Anthropic provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/anthropic/). The API key is never stored in your code or in environment variables: it lives in [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html) and the agent fetches it at runtime with the `@requires_api_key` decorator.

Inside `CalculatorLab/`, add a second Runtime and copy the code:

```bash
agentcore add runtime --name anthropic_agent --language python
cp ../agent_anthropic/main.py ../agent_anthropic/pyproject.toml app/anthropic_agent/
```

Store your Anthropic API key as an AgentCore Identity credential. Write the key to a file (the CLI rejects inline values) and pass the file:

```bash
printf '%s' "YOUR-ANTHROPIC-APIKEY" > anthropic.key
agentcore add credentials api-key --name AnthropicKey --api-key file://anthropic.key
rm anthropic.key
```

The CLI passes the credential provider name to the deployed Runtime as `CREDENTIAL_ANTHROPICKEY_NAME`, which the agent reads. It also saves the key in `agentcore/.env.local` (gitignored) as `AGENTCORE_CREDENTIAL_ANTHROPICKEY`, so `agentcore dev` works locally without extra setup.

Deploy and test:

```bash
agentcore deploy
agentcore invoke --runtime anthropic_agent \
  --session-id anthropic-session-test-123456789012 \
  --payload '{"prompt": "Hello! What can you do?"}'
```

To learn how to deploy with other model providers using Strands Agents, check out the [Strands Agents documentation](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/amazon-bedrock/).

## Step 12: Clean Up

When you're done experimenting, remove the resources from the project and deploy the empty project to delete the stack:

```bash
agentcore remove all --yes
agentcore deploy --yes
```

This removes:
- AgentCore Runtime deployment
- Auto-created IAM roles
- AgentCore Identity credentials created by the project

The Runtime's CloudWatch log groups (`/aws/bedrock-agentcore/runtimes/...`) are kept. Delete them from the CloudWatch console if you don't need them.

