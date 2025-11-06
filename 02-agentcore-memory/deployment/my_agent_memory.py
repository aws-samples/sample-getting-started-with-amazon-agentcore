"""
Production-Ready AI Agent with Memory
Remembers conversations and user preferences across sessions
"""
import os
from strands import Agent
from strands_tools import calculator
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

app = BedrockAgentCoreApp()

MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")

# Global agent instance
_agent = None

def get_or_create_agent(actor_id: str, session_id: str) -> Agent:
    """
    Get existing agent or create new one with memory configuration.
    Since the container is pinned to the session ID, we only need one agent per container.
    """
    global _agent
    
    if _agent is None:
        # Configure memory with retrieval for user facts and preferences
        memory_config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config={
                f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.5),
                f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.5)
            }
        )
        
        # Create agent with memory session manager
        _agent = Agent(
            model=MODEL_ID,
            session_manager=AgentCoreMemorySessionManager(memory_config, REGION),
            system_prompt="You are a helpful assistant with memory. Remember user preferences and facts across conversations. Use the calculate tool for math problems.",
            tools=[calculator]
        )
    
    return _agent

@app.entrypoint
def invoke(payload, context):
    """AgentCore Runtime entry point with lazy-loaded agent"""
    if not MEMORY_ID:
        return {"error": "Memory not configured. Set BEDROCK_AGENTCORE_MEMORY_ID environment variable."}
    
    # Extract session and actor information
    actor_id = context.request_headers.get('X-Amzn-Bedrock-AgentCore-Runtime-Custom-Actor-Id', 'user') if context.request_headers else 'user'
    session_id = context.session_id or 'default_session'
    
    # Get or create agent (lazy loading)
    agent = get_or_create_agent(actor_id, session_id)
    
    prompt = payload.get("prompt", "Hello!")
    result = agent(prompt)
    
    return {
        "response": result.message.get('content', [{}])[0].get('text', str(result))
    }

if __name__ == "__main__":
    app.run()

