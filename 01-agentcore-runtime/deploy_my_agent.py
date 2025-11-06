#!/usr/bin/env python3

from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import os

def deploy():
    """Deploy the LangGraph agent"""
    boto_session = Session()
    region = boto_session.region_name
    
    agentcore_runtime = Runtime()
    
    # Check for required ENTRYPOINT environment variable
    entrypoint = os.getenv("ENTRYPOINT")
    if not entrypoint:
        print("Error: ENTRYPOINT environment variable is required.")
        print("Please set it before running this script:")
        print("export ENTRYPOINT=deployment/my_agent.py")
        exit(1)
    
    agent_name = entrypoint.split(".")[0]
    
    print(f"Deploying LangGraph agent to {region}...")
    
    # Configure
    agentcore_runtime.configure(
        entrypoint=entrypoint,
        auto_create_execution_role=True,
        auto_create_ecr=True,
        requirements_file="requirements.txt", 
        region=region,
        agent_name=agent_name
    )
            
    # Launch
    result = agentcore_runtime.launch()
    print(f"✅ Agent deployed: {result.agent_arn}")
    
    return result

if __name__ == "__main__":
    deploy()
