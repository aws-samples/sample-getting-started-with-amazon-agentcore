"""
Production-Ready AI Agent with Memory
Remembers conversations and user preferences across sessions
"""
import os
from strands import Agent
from strands_tools import calculator
from bedrock_agentcore import BedrockAgentCoreApp, RequestContext
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
import json

app = BedrockAgentCoreApp()

MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.getenv("AWS_REGION", "us-west-2")
MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
# HTTP headers are normalized to lowercase
CUSTOM_HEADER_NAME = 'x-amzn-bedrock-agentcore-runtime-custom-actor-id'

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
def invoke(payload, context: RequestContext):
    """AgentCore Runtime entry point with lazy-loaded agent"""
    app.logger.info("Payload: %s", payload)
    app.logger.info("Context: %s", context)
    
    if not MEMORY_ID:
        return {"error": "Memory not configured. Set BEDROCK_AGENTCORE_MEMORY_ID environment variable."}

    # Extract custom header and session information
    actor_id = 'default-user'
    if context and hasattr(context, 'request_headers') and context.request_headers:
        # Headers are normalized to lowercase
        actor_id = context.request_headers.get(CUSTOM_HEADER_NAME)
        app.logger.info("Request headers: %s", json.dumps(context.request_headers))
        app.logger.info("Actor ID extracted from header '%s': %s", CUSTOM_HEADER_NAME, actor_id)
    else:
        app.logger.warning("No request headers found in context")
    
    session_id = context.session_id
    app.logger.info("Using actor_id='%s', session_id='%s'", actor_id, session_id)
    print("actor_id: ", actor_id)
    print("session_id: ", session_id)
    
    # Get or create agent (lazy loading)
    agent = get_or_create_agent(actor_id, session_id)
    
    prompt = payload.get("prompt", "Hello!")
    result = agent(prompt)
    
    return {
        "response": result.message.get('content', [{}])[0].get('text', str(result))
    }

if __name__ == "__main__":
    app.run()