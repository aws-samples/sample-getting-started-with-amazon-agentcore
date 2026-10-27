import os

from bedrock_agentcore.identity.auth import requires_api_key
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models.anthropic import AnthropicModel

# Name of the AgentCore Identity API key provider. The AgentCore CLI injects it as
# CREDENTIAL_<NAME>_NAME when you run `agentcore add credentials api-key --name AnthropicKey`.
IDENTITY_PROVIDER_NAME = os.environ.get("CREDENTIAL_ANTHROPICKEY_NAME", "AnthropicKey")

# Local development only: `agentcore add credentials api-key` also writes the key to
# agentcore/.env.local, and `agentcore dev` loads it as this variable.
LOCAL_API_KEY_ENV_VAR = "AGENTCORE_CREDENTIAL_ANTHROPICKEY"

MODEL_ID = os.getenv("MODEL_ID", "claude-sonnet-5-5")  # https://docs.claude.com/en/docs/about-claude/models/overview


@requires_api_key(provider_name=IDENTITY_PROVIDER_NAME)
def _api_key_from_identity(api_key: str) -> str:
    """Fetch the Anthropic API key from AgentCore Identity (deployed runtime)."""
    return api_key


def get_api_key() -> str:
    """Return the API key: from .env.local when running `agentcore dev`, from AgentCore Identity when deployed."""
    if os.getenv("LOCAL_DEV") == "1":
        api_key = os.getenv(LOCAL_API_KEY_ENV_VAR)
        if not api_key:
            raise RuntimeError(
                f"{LOCAL_API_KEY_ENV_VAR} not found. Add {LOCAL_API_KEY_ENV_VAR}=your-key to agentcore/.env.local"
            )
        return api_key
    return _api_key_from_identity()


def create_model() -> AnthropicModel:
    """Create the Anthropic model with the API key"""
    return AnthropicModel(
        client_args={"api_key": get_api_key()},
        max_tokens=4000,
        model_id=MODEL_ID,
        params={
            "temperature": 0.3,
        },
    )


# Create an agent instance (lazy loaded on the first invocation)
agent = None


def create_agent():
    global agent
    if agent is None:
        agent = Agent(model=create_model())
    return agent


# Initialize the Bedrock AgentCore application
app = BedrockAgentCoreApp()


# Define the main entry point for the agent
@app.entrypoint
def invoke(payload):
    """Your AI agent function"""
    # Extract the user message from payload, with a default greeting if not provided
    user_message = payload.get("prompt", "Hello! How can I help you today?")

    # Process the user message through the agent
    agent = create_agent()
    result = agent(user_message)

    # Return the agent's response in the expected format
    return {"response": result.message.get('content', [{}])[0].get('text', str(result))}


# Execute the application when the script is run directly
if __name__ == "__main__":
    app.run()
