import boto3
import json
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.analytics_tools import detect_performance_anomalies

class MasterAgent:
    def __init__(self, model_id="anthropic.claude-3-sonnet-20240229-v1:0"):
        # The region will be picked up from the environment variables
        self.bedrock_client = boto3.client(service_name='bedrock-runtime')
        self.model_id = model_id
        self.tools = [
            {
                "toolSpec": {
                    "name": "detect_performance_anomalies",
                    "description": "Identifies statistical deviations in time-series KPI data.",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {
                                "kpi_name": {
                                    "type": "string",
                                    "description": "The name of the Key Performance Indicator (KPI) to analyze."
                                },
                                "time_window": {
                                    "type": "string",
                                    "description": "The time window for the analysis (e.g., '24h', '7d')."
                                }
                            },
                            "required": ["kpi_name", "time_window"]
                        }
                    }
                }
            }
        ]

    def run(self, user_query):
        print(f"Master Agent received query: {user_query}")

        # Create the message payload for Bedrock
        messages = [{"role": "user", "content": [{"text": user_query}]}]
        
        # Invoke Bedrock with the tool configuration
        response = self.bedrock_client.converse(
            modelId=self.model_id,
            messages=messages,
            toolConfig={"tools": self.tools}
        )
        
        response_message = response['output']['message']
        
        # Check if the model wants to use a tool
        tool_calls = [content for content in response_message['content'] if 'toolUse' in content]
        
        if tool_calls:
            print("Bedrock wants to use a tool.")
            # For this example, we'll just handle the first tool call
            tool_call = tool_calls[0]['toolUse']
            tool_name = tool_call['name']
            tool_args = tool_call['input']
            
            print(f"Tool to call: {tool_name}")
            print(f"Tool arguments: {tool_args}")
            
            # Call the appropriate tool
            if tool_name == "detect_performance_anomalies":
                tool_result = detect_performance_anomalies(**tool_args)
                
                # Append the tool result to the conversation history
                messages.append(response_message)
                messages.append({
                    "role": "user",
                    "content": [{
                        "toolResult": {
                            "toolUseId": tool_call['toolUseId'],
                            "content": [{"json": json.loads(tool_result)}]
                        }
                    }]
                })
                
                # Call Bedrock again with the tool result to get a natural language response
                final_response = self.bedrock_client.converse(
                    modelId=self.model_id,
                    messages=messages,
                    toolConfig={"tools": self.tools}
                )
                
                return final_response['output']['message']['content'][0]['text']
            else:
                return f"Error: Tool '{tool_name}' is not defined."
        else:
            print("Bedrock did not request to use a tool.")
            return response_message['content'][0]['text']


if __name__ == '__main__':
    # Example usage:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='../.env') # To run this file directly for testing
    master_agent = MasterAgent()
    user_query = "Are there any performance anomalies for RRC_Setup_Success_Rate in the last 24 hours?"
    response = master_agent.run(user_query)
    print("\nFinal Response:")
    print(response)
