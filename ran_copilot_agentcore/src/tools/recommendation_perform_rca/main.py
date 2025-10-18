import json
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add the parent 'src' directory to the Python path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from shared.athena import run_athena_query

# --- Configuration ---
AWS_REGION = "ap-south-1"
DATABASE_NAME = "ran_copilot_db"
S3_OUTPUT_LOCATION = "s3://ran-copilot-data-lake/athena-query-results-tool/"

def handler(event, context):
    """
    This Lambda function performs a root cause analysis for a given problem on a cell.
    For this implementation, it checks for recent critical alarms on the specified cell.
    """
    load_dotenv()
    athena = boto3.client('athena', region_name=AWS_REGION)

    cell_id = event.get('cell_id')
    problem = event.get('problem', 'Unknown Performance Issue')
    time_window_hours = event.get('time_window_hours', 24)
    
    if not cell_id:
        return {'statusCode': 400, 'body': json.dumps({"error": "cell_id is a required parameter."})}

    print(f"RCA Tool Lambda: Performing RCA for '{problem}' on cell '{cell_id}' in the last {time_window_hours} hours.")
    
    # Calculate the start time for the query
    start_time = datetime.utcnow() - timedelta(hours=time_window_hours)
    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

    query = f"""
    SELECT 
        alarm_name,
        severity,
        "timestamp"
    FROM 
        fault_management_alarms
    WHERE
        cell_id = '{cell_id}'
        AND severity = 'Critical'
        AND "timestamp" > CAST('{start_time_str}' AS timestamp)
    ORDER BY
        "timestamp" DESC
    LIMIT 5
    """
    
    try:
        query_results = run_athena_query(athena, query, DATABASE_NAME, S3_OUTPUT_LOCATION)
        
        if not query_results:
            response_body = {
                "likely_cause": "Undetermined",
                "evidence": "No critical alarms found for this cell in the specified time window."
            }
        else:
            most_recent_alarm = query_results[0]
            response_body = {
                "likely_cause": "Recent_Critical_Alarm",
                "evidence": f"A critical alarm '{most_recent_alarm['alarm_name']}' was found at {most_recent_alarm['timestamp']}."
            }

        return {
            'statusCode': 200,
            'body': json.dumps(response_body, indent=2)
        }
    except Exception as e:
        print(f"Error executing query: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }

if __name__ == '__main__':
    # We need to test with a cell_id that exists in our simulated fault data
    test_event = {"cell_id": "cell_A", "problem": "High_RRC_Failure_Rate"}
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
