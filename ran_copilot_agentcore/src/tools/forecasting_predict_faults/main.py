import json
import os
import random
from dotenv import load_dotenv

def handler(event, context):
    """
    This Lambda function simulates predicting the probability of an equipment fault.
    In a real-world scenario, this would invoke a pre-trained ML model.
    """
    load_dotenv()

    cell_id = event.get('cell_id')
    time_horizon = event.get('time_horizon', '7_days')
    
    if not cell_id:
        return {'statusCode': 400, 'body': json.dumps({"error": "cell_id is a required parameter."})}

    print(f"PredictFault Tool: Predicting fault probability for cell '{cell_id}' in the next {time_horizon}.")
    
    # Mocked prediction logic
    # A real implementation would use a model to calculate this probability.
    # We'll generate a random probability and contributing factors for demonstration.
    fault_probability = round(random.uniform(0.05, 0.95), 2)
    
    possible_factors = [
        "High_Temperature_Alarms",
        "Increased_Handover_Failures",
        "High_VSWR_Warnings",
        "Anomalous_UL_BLER"
    ]
    
    # Select 1 or 2 random factors
    num_factors = random.randint(1, 2)
    contributing_factors = random.sample(possible_factors, num_factors)
    
    response_body = {
        "fault_probability": fault_probability,
        "contributing_factors": contributing_factors
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "cell_id": "cell_B",
        "time_horizon": "7_days"
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
