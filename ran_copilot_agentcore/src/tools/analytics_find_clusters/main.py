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
    This Lambda function queries Athena to find clusters of degraded cells,
    defined as cells with an average RSRP below a certain threshold.
    """
    load_dotenv()
    athena = boto3.client('athena', region_name=AWS_REGION)

    # In a real tool, this might be a parameter. For now, we'll hardcode it.
    rsrp_threshold = event.get('rsrp_threshold', -105) 
    
    print(f"AnalyticsTool Lambda: Finding degraded cell clusters with avg RSRP < {rsrp_threshold}")
    
    query = f"""
    SELECT 
        cluster_id, 
        ue_id, 
        AVG(rsrp) as avg_rsrp, 
        AVG(dl_bler) as avg_dl_bler
    FROM 
        analytics_ue_metrics
    WHERE
        cluster_id IS NOT NULL 
        AND ue_id IS NOT NULL
    GROUP BY 
        cluster_id, ue_id
    HAVING 
        AVG(rsrp) < {rsrp_threshold}
    ORDER BY 
        avg_rsrp ASC
    LIMIT 20;
    """
    
    try:
        query_results = run_athena_query(athena, query, DATABASE_NAME, S3_OUTPUT_LOCATION)
        
        response_body = {"degraded_cells": query_results}
        
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
    test_event = {"rsrp_threshold": -105}
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
