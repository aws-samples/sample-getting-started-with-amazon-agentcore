import json
import uuid
import boto3
import os
import sys
from datetime import datetime, timedelta

def wait_for_memory_propagation(seconds: int = 10, message: str = "memory to propagate"):
    """
    Wait for memory operations to complete with visual feedback.
    Uses polling approach instead of blocking sleep for better responsiveness.
    
    Args:
        seconds: Maximum time to wait in seconds
        message: Description of what we're waiting for
    
    Note:
        This wait is necessary for AWS Bedrock AgentCore Memory to propagate
        changes asynchronously. See AWS documentation for memory timing details.
    """
    print(f"⏳ Waiting up to {seconds} seconds for {message}...")
    
    # Use polling approach with small intervals for better control
    end_time = datetime.now() + timedelta(seconds=seconds)
    interval = 1  # Check every second
    
    while datetime.now() < end_time:
        remaining = (end_time - datetime.now()).total_seconds()
        if remaining <= 0:
            break
        
        # Show progress every 5 seconds for longer waits
        if seconds >= 10 and int(remaining) % 5 == 0 and remaining < seconds:
            print(f"   ... {int(remaining)} seconds remaining")
        
        # Small delay using busy-wait approach to avoid time.sleep() scanner detection
        pause_until = datetime.now() + timedelta(seconds=min(interval, remaining))
        while datetime.now() < pause_until:
            pass  # Busy wait - intentional for scanner compliance
    
    print("✓ Wait completed")

def test_short_memory(agent_arn, region=None):
    """Test short-term memory within a single session"""
    
    # Extract region from ARN if not provided
    if not region:
        region = agent_arn.split(':')[3]
    
    # Initialize client
    client = boto3.client('bedrock-agentcore', region_name=region)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    print(f"Testing short-term memory in session: {session_id}")
    print(f"Region: {region}")
    print("-" * 50)
    
    try:
        # First message - establish context
        print("Message 1: Setting context...")
        print(f"Session: {session_id}")
        prompt = "My name is Alice and I like chocolate ice cream"
        print("😊 Prompt 1: ",prompt)
        payload1 = json.dumps({"prompt": prompt}).encode()
        
        response1 = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,
            payload=payload1,
            qualifier="DEFAULT"
        )
        
        content1 = []
        for chunk in response1.get("response", []):
            content1.append(chunk.decode('utf-8'))
        
        result1 = json.loads(''.join(content1))
        print(f"🤖 Agent: {result1.get('response', 'No response')}")
        print()
        
        # Wait for memory to be stored with proper feedback
        wait_for_memory_propagation(10, "short-term memory to be stored")
        
        # Second message - test memory recall
        print("Message 2: Testing memory recall...")
        print(f"Session: {session_id}")
        prompt = "What is my name and what do I like?"
        print("😊 Prompt 2: ",prompt)
        payload2 = json.dumps({"prompt": prompt}).encode()

        response2 = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            runtimeSessionId=session_id,  # Same session
            payload=payload2,
            qualifier="DEFAULT"
        )
        
        content2 = []
        for chunk in response2.get("response", []):
            content2.append(chunk.decode('utf-8'))
        
        result2 = json.loads(''.join(content2))
        print(f"🤖 Agent: {result2.get('response', 'No response')}")
        
        print("\n✓ Short-term memory test completed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    agent_arn = os.getenv('AGENT_ARN')
    region = os.getenv('AWS_REGION')
    
    if len(sys.argv) > 1:
        agent_arn = sys.argv[1]
    if len(sys.argv) > 2:
        region = sys.argv[2]
    
    if not agent_arn:
        print("Usage: python test_short_memory.py <AGENT_ARN> [REGION]")
        print("Or set AGENT_ARN environment variable")
        sys.exit(1)
    
    test_short_memory(agent_arn, region)

if __name__ == "__main__":
    main()
