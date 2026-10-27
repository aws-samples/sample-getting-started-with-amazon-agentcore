"""
Production-Ready AI Agent with Memory
Remembers conversations and user preferences across sessions
"""
import os
from strands import Agent
from strands_tools import calculator
from bedrock_agentcore.runtime import BedrockAgentCoreApp, RequestContext
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

app = BedrockAgentCoreApp()

# The AgentCore CLI injects MEMORY_<NAME>_ID for each memory in the project.
# This lab creates a memory named "LabMemory" (`agentcore add memory --name LabMemory`).
MEMORY_ID = os.getenv("MEMORY_LABMEMORY_ID")
REGION = os.getenv("AWS_REGION", "us-west-2")
MODEL_ID = os.getenv("MODEL_ID", "global.anthropic.claude-sonnet-5-5")
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
        # relevance_score is the minimum similarity score; natural questions often score ~0.3-0.4
        memory_config = AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config={
                f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.2),
                f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.2)
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

if __name__ == "__main__":
    app.run()