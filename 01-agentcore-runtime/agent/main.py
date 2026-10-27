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
