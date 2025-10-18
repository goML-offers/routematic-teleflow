from strands.services.bedrock import Bedrock
from strands.agent.agent import Agent
from strands.models import Message, MessageHistory
from strands.tools import tool

import sys
import os

# Add the tools directory to the python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from tools.analytics_tool import handler as detect_performance_anomalies_handler

@tool()
def detect_performance_anomalies(kpi_name: str, time_window: str) -> dict:
    """
    Identifies statistical deviations in time-series KPI data.
    
    :param kpi_name: The name of the Key Performance Indicator (KPI) to analyze.
    :param time_window: The time window for the analysis (e.g., '24h', '7d').
    :return: A dictionary containing a list of performance anomalies.
    """
    # This is a local invocation of the tool's handler for demonstration.
    # When deployed, AgentCore Gateway would invoke the Lambda function directly.
    event = {"arguments": {"kpi_name": kpi_name, "time_window": time_window}}
    response = detect_performance_anomalies_handler(event, None)
    return response

# The main handler function for the Strands agent
def handler(event, context):
    """
    This is the main entry point for the agent when deployed on AWS Lambda
    or a similar serverless environment.
    """
    # In a real deployment, the input event would be parsed here.
    # For now, we'll use a hardcoded query for development.
    user_query = "Are there any performance anomalies for RRC_Setup_Success_Rate in the last 24 hours?"
    
    # Initialize the Bedrock service with the Nova Pro model
    bedrock = Bedrock(model_id="amazon.nova-pro-v1:0")

    # Create an agent instance and attach the tool
    agent = Agent(
        bedrock,
        system_prompt="You are a helpful assistant for Radio Access Network (RAN) engineers.",
        tools=[detect_performance_anomalies]
    )

    # Create a message history and add the user's query
    message_history = MessageHistory()
    message_history.add_message(Message(role="user", content=user_query))

    # Get the response from the agent
    response = agent.get_response(message_history)
    
    # Print the response for now
    # In a real deployment, this would be returned as the handler's output.
    print(f"Agent Response: {response}")

    return {
        'statusCode': 200,
        'body': response
    }

# This allows for local testing of the handler
if __name__ == '__main__':
    handler(None, None)
