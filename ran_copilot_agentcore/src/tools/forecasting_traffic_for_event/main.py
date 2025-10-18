import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add the parent 'src' directory to the Python path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Note: No Athena query needed for this mock

def handler(event, context):
    """
    This Lambda function simulates a time-series forecast for traffic demand.
    In a real-world scenario, this would invoke a pre-trained ML model (e.g., on SageMaker).
    """
    load_dotenv()

    location = event.get('location')
    event_time_str = event.get('event_time')
    event_type = event.get('event_type', 'generic_event')
    
    if not location or not event_time_str:
        return {'statusCode': 400, 'body': json.dumps({"error": "location and event_time are required."})}

    print(f"ForecastTool: Forecasting traffic for a '{event_type}' at '{location}'.")
    
    # Mocked forecast logic
    # A real implementation would use a model to generate this time series.
    try:
        event_time = datetime.fromisoformat(event_time_str)
    except ValueError:
        return {'statusCode': 400, 'body': json.dumps({"error": "Invalid event_time format. Please use ISO 8601 format."})}

    forecast_timeseries = []
    # Generate a simple mock forecast for the 3 hours around the event
    for i in range(-1, 3):
        timestamp = event_time + timedelta(hours=i)
        # Simulate a traffic peak around the event time
        peak_multiplier = max(0, 1 - abs(i - 0.5) / 2)
        predicted_traffic_gb = round(100 + (250 * peak_multiplier), 2) # Base traffic + peak
        
        forecast_timeseries.append({
            "timestamp": timestamp.isoformat(),
            "predicted_traffic_gb": predicted_traffic_gb
        })

    response_body = {"forecast_timeseries": forecast_timeseries}

    return {
        'statusCode': 200,
        'body': json.dumps(response_body, indent=2)
    }

if __name__ == '__main__':
    test_event = {
        "location": "stadium_coordinates",
        "event_time": "2025-12-31T20:00:00",
        "event_type": "sports_game"
    }
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
