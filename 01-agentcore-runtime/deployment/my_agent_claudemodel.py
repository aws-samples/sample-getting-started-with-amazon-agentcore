from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models.anthropic import AnthropicModel
import os

def create_model():
    """Create the AnthropicModel model with the API key"""
    return  AnthropicModel(
        client_args={
            "api_key": os.environ["CLAUDE_APIKEY"]
        },
        # **model_config
        max_tokens=4000,
        model_id="claude-3-5-haiku-20241022", #https://docs.claude.com/en/docs/about-claude/models/overview - https://docs.claude.com/en/api/rate-limits
        params={
            "temperature": 0.3,
        }
    )

# Create an agent instance
agent = None

def create_agent():
    global agent
    if agent is None:
        agent = Agent(model=create_model()
                        )
    return agent


# Initialize the Bedrock Agent Core application
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
