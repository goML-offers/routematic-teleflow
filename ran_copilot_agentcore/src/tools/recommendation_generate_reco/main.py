import json
import os
import uuid
from dotenv import load_dotenv

def handler(event, context):
    """
    This Lambda function consumes the output of RCA and simulation tools to
    formulate a structured, actionable recommendation.
    This is a mock implementation.
    """
    load_dotenv()

    rca_result = event.get('rca_result', {})
    simulation_result = event.get('simulation_result', {})
    
    if not rca_result or not simulation_result:
        return {'statusCode': 400, 'body': json.dumps({"error": "rca_result and simulation_result are required."})}

    print(f"GenerateReco Tool: Generating recommendation based on RCA and simulation.")
    
    # Mocked recommendation logic
    # A real implementation would have more sophisticated logic to build the recommendation.
    
    recommendation_id = f"REC-{str(uuid.uuid4())[:8].upper()}"
    
    title = "Revert Parameter Change to Resolve Critical Alarms"
    justification = f"Root cause analysis identified a likely cause: '{rca_result.get('likely_cause')}'. Evidence: {rca_result.get('evidence')}. " \
                    f"A simulation of a corrective action predicts the following impact: {json.dumps(simulation_result.get('predicted_impact'))}"
    
    steps = [
        "1. Create a trouble ticket to track the issue.",
        "2. Generate the configuration script to revert the parameter change.",
        "3. Apply the script during a maintenance window.",
        "4. Monitor KPIs post-change to ensure resolution."
    ]

    response_body = {
        "recommendation_id": recommendation_id,
        "title": title,
        "justification": justification,
        "steps": steps
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "rca_result": {
            "likely_cause": "Recent_Critical_Alarm",
            "evidence": "A critical alarm 'High_Temperature' was found."
        },
        "simulation_result": {
            "predicted_impact": [
                {'kpi': 'RRC_Success_Rate', 'change': '+2.5%'}
            ]
        }
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
