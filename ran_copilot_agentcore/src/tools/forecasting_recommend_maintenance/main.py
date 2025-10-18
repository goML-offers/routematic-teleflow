import json
import os
from dotenv import load_dotenv

def handler(event, context):
    """
    This Lambda function consumes a fault prediction and generates a
    specific, actionable maintenance recommendation.
    This is a mock implementation.
    """
    load_dotenv()

    fault_prediction_result = event.get('fault_prediction_result', {})
    
    if not fault_prediction_result:
        return {'statusCode': 400, 'body': json.dumps({"error": "fault_prediction_result is required."})}

    print(f"RecommendMaint Tool: Generating maintenance recommendation.")
    
    # Mocked recommendation logic
    probability = fault_prediction_result.get('fault_probability', 0)
    factors = fault_prediction_result.get('contributing_factors', [])
    
    recommendation = "No maintenance required at this time." # Default
    
    if probability > 0.9:
        recommendation = f"URGENT: Immediate inspection required. High probability ({probability*100}%) of imminent fault. Key factors: {', '.join(factors)}."
    elif probability > 0.7:
        recommendation = f"HIGH PRIORITY: Schedule technician to inspect equipment within the next 48 hours. Probability of fault is high ({probability*100}%). Key factors: {', '.join(factors)}."
    elif probability > 0.5:
        recommendation = f"MEDIUM PRIORITY: Add equipment to the next scheduled maintenance cycle for inspection. Moderate ({probability*100}%) fault probability detected. Key factors: {', '.join(factors)}."
    else:
        recommendation = f"LOW PRIORITY: Continue to monitor. Fault probability is low ({probability*100}%)."

    response_body = {
        "recommendation": recommendation
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "fault_prediction_result": {
            "fault_probability": 0.83,
            "contributing_factors": ["High_VSWR_Warnings", "Anomalous_UL_BLER"]
        }
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
