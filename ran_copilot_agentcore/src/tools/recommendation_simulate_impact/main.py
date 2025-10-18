import json
import os
from dotenv import load_dotenv

def handler(event, context):
    """
    This Lambda function simulates the impact of a proposed parameter change on key KPIs.
    In a real-world scenario, this would invoke a pre-trained ML model.
    For this implementation, it returns a hardcoded, mock prediction.
    """
    load_dotenv()

    cell_id = event.get('cell_id')
    parameter_change = event.get('parameter_change', {})
    
    if not cell_id or not parameter_change:
        return {'statusCode': 400, 'body': json.dumps({"error": "cell_id and parameter_change are required."})}

    param_name = parameter_change.get('name')
    new_value = parameter_change.get('new_value')

    print(f"SimulateImpact Tool: Simulating impact of changing '{param_name}' to '{new_value}' on cell '{cell_id}'.")
    
    # Mocked prediction logic
    # A real implementation would pass these inputs to a SageMaker endpoint or similar.
    if param_name == "TX_Power":
        predicted_impact = [
            {'kpi': 'RRC_Success_Rate', 'change': '+1.5%'},
            {'kpi': 'Handover_Success_Rate', 'change': '-0.2%'},
            {'kpi': 'Coverage', 'change': '+3.0%'}
        ]
    else:
        predicted_impact = [
            {'kpi': 'RRC_Success_Rate', 'change': '+0.5%'},
            {'kpi': 'Handover_Success_Rate', 'change': '+0.1%'}
        ]

    response_body = {"predicted_impact": predicted_impact}

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "cell_id": "cell_A",
        "parameter_change": {
            "name": "TX_Power",
            "new_value": 41
        }
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
