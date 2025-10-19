"""
RAN Co-pilot Client
Demonstrates how to invoke the deployed Strands Agent through AgentCore Runtime.
"""
import boto3
import json
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

class RANCopilorClient:
    """Client for interacting with the RAN Co-pilot Agent deployed on AgentCore Runtime."""
    
    def __init__(self, agent_runtime_arn: str, region: str = "ap-south-1"):
        """
        Initialize the RAN Co-pilot client.
        
        Args:
            agent_runtime_arn: ARN of the deployed agent runtime
            region: AWS region
        """
        self.agent_runtime_arn = agent_runtime_arn
        self.region = region
        self.client = boto3.client('bedrock-agentcore', region_name=region)
        
    def invoke_agent(self, prompt: str, session_id: str = "default-session-001") -> Dict[str, Any]:
        """
        Invoke the RAN Co-pilot Agent with a user prompt.
        
        Args:
            prompt: User query or instruction
            session_id: Session identifier (must be 33+ characters for AgentCore)
            
        Returns:
            Agent response
        """
        # Ensure session ID is at least 33 characters
        if len(session_id) < 33:
            session_id = session_id + "-" + "x" * (33 - len(session_id))
        
        try:
            print(f"\n{'='*70}")
            print(f"Invoking Agent with prompt: {prompt}")
            print(f"Session ID: {session_id}")
            print(f"{'='*70}")
            
            payload = json.dumps({
                "input": {
                    "prompt": prompt
                }
            })
            
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_runtime_arn,
                runtimeSessionId=session_id,
                payload=payload,
                qualifier="DEFAULT"
            )
            
            # Read and parse the response
            response_body = response['response'].read()
            response_data = json.loads(response_body)
            
            print(f"\nAgent Response:")
            print(json.dumps(response_data, indent=2, default=str))
            
            return response_data
            
        except Exception as e:
            print(f"Error invoking agent: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

def test_agent():
    """Test the RAN Co-pilot Agent with various scenarios."""
    
    # Get agent ARN from environment or command line
    agent_arn = os.getenv('AGENT_RUNTIME_ARN')
    if not agent_arn:
        print("ERROR: AGENT_RUNTIME_ARN environment variable not set")
        print("Please set it to your AgentCore Runtime ARN")
        return
    
    # Initialize client
    client = RANCopilorClient(agent_arn)
    
    # Test scenarios
    test_prompts = [
        # Analytics queries
        "Are there any performance anomalies in RSRP over the last 24 hours?",
        "Find cell clusters with degraded performance",
        "What's the correlation between customer experience and signal strength?",
        "Check if any network slices are experiencing congestion",
        
        # Recommendation queries
        "Analyze the root cause of the performance issues we just found",
        "What would happen if we increased the antenna tilt by 5 degrees on cell_001?",
        "Generate optimization recommendations for our network",
        
        # Automation queries
        "Create a trouble ticket for the high interference issue with severity critical",
        
        # Forecasting queries
        "Forecast network traffic for the New Year's Eve event on 2025-01-01 in Mumbai",
        "Predict potential equipment faults in our network",
        "Recommend preventive maintenance actions"
    ]
    
    print("\n" + "="*70)
    print("RAN CO-PILOT AGENT - TEST SUITE")
    print("="*70)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[TEST {i}/{len(test_prompts)}]")
        client.invoke_agent(prompt, f"test-session-{i:02d}")
        print("\n" + "-"*70)

def interactive_mode():
    """Run the client in interactive mode."""
    
    agent_arn = os.getenv('AGENT_RUNTIME_ARN')
    if not agent_arn:
        print("ERROR: AGENT_RUNTIME_ARN environment variable not set")
        return
    
    client = RANCopilorClient(agent_arn)
    session_counter = 0
    
    print("\n" + "="*70)
    print("RAN CO-PILOT AGENT - INTERACTIVE MODE")
    print("="*70)
    print("\nType your queries below. Enter 'exit' to quit.\n")
    
    while True:
        try:
            prompt = input("RAN Co-pilot> ").strip()
            if prompt.lower() == 'exit':
                print("Exiting...")
                break
            if not prompt:
                continue
            
            session_counter += 1
            client.invoke_agent(prompt, f"interactive-session-{session_counter:03d}")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        # Run test suite
        test_agent()
