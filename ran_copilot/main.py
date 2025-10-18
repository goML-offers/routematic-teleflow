from agents.master_agent import MasterAgent
from dotenv import load_dotenv
import os

def main():
    """
    Main function to run the CLI for the RAN Co-pilot.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for AWS credentials
    if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
        print("Error: AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file.")
        return
        
    print("Welcome to the RAN Co-pilot CLI.")
    print("You can start by asking questions about your RAN network.")
    print("Type 'exit' to quit.")
    
    master_agent = MasterAgent()
    
    while True:
        user_query = input("\n> ")
        if user_query.lower() == 'exit':
            break
        
        response = master_agent.run(user_query)
        print(f"\nCo-pilot: {response}")

if __name__ == '__main__':
    main()
