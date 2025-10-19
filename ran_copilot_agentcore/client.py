import boto3
import uuid
import os
from dotenv import load_dotenv

# --- Configuration ---
AGENT_ID = "YOUR_AGENT_ID"  # <-- PASTE YOUR AGENT ID HERE
AGENT_ALIAS_ID = "YOUR_AGENT_ALIAS_ID" # <-- PASTE YOUR AGENT ALIAS ID HERE
AWS_REGION = "ap-south-1"

def main():
    """
    Main function to run the CLI for interacting with the deployed RAN Co-pilot agent.
    """
    load_dotenv()
    
    # Check for AWS credentials
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        print("Error: AWS credentials not found. Please set them in your .env file or environment.")
        return
        
    # Initialize the Bedrock Agent Runtime client
    bedrock_agent_runtime = boto3.client(
        'bedrock-agent-runtime',
        region_name=AWS_REGION
    )

    # Create a unique session ID for the conversation
    session_id = str(uuid.uuid4())

    print("--- RAN Co-pilot Client ---")
    print(f"Agent ID: {AGENT_ID}")
    print(f"Session ID: {session_id}")
    print("Type 'exit' to quit.")
    print("---------------------------")

    while True:
        user_query = input("\n> ")
        if user_query.lower() == 'exit':
            break
        
        try:
            # Invoke the agent
            response = bedrock_agent_runtime.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=session_id,
                inputText=user_query,
            )

            # Process the streaming response
            completion = ""
            for event in response.get("completion"):
                chunk = event["chunk"]
                completion += chunk["bytes"].decode()
            
            print(f"\nCo-pilot: {completion}")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
