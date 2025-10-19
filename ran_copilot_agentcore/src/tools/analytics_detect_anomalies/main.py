import json
import boto3
import os
from dotenv import load_dotenv

# Add the parent 'src' directory to the Python path to allow absolute imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from shared.athena import run_athena_query

# --- Configuration ---
AWS_REGION = "ap-south-1"
DATABASE_NAME = "ran_copilot_db"
S3_OUTPUT_LOCATION = "s3://ran-copilot-data-lake/athena-query-results-tool/"

def handler(event, context):
    """
    This Lambda function queries the analytics_ue_metrics table in Athena
    to find performance anomalies.
    """
    load_dotenv()
    athena = boto3.client('athena', region_name=AWS_REGION)

    kpi_name = event.get('kpi_name', 'rsrp')
    
    print(f"AnalyticsTool Lambda: Querying for anomalies related to KPI: {kpi_name}")
    
    # In a real scenario, the query would be more complex. For now, we find poor RSRP.
    query = f"""
    SELECT ue_id, cluster_id, slicing_id, time, rsrp
    FROM analytics_ue_metrics
    WHERE rsrp < -110
      AND ue_id IS NOT NULL
      AND cluster_id IS NOT NULL
    LIMIT 10;
    """
    
    try:
        query_results = run_athena_query(athena, query, DATABASE_NAME, S3_OUTPUT_LOCATION)
        
        response_body = {"anomalies": query_results}
        
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
    # This block allows local testing of the Lambda function.
    test_event = {"kpi_name": "rsrp"}
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
