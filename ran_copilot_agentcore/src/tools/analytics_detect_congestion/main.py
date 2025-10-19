import json
import boto3
import os
from dotenv import load_dotenv

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
    This Lambda function analyzes slice performance to detect congestion.
    For this implementation, we define congestion as high Downlink BLER (Block Error Rate).
    """
    load_dotenv()
    athena = boto3.client('athena', region_name=AWS_REGION)

    slice_name = event.get('slice_name', 'slicing_1') 
    bler_threshold = event.get('bler_threshold', 0.1) # 10% BLER
    
    print(f"AnalyticsTool Lambda: Detecting congestion in '{slice_name}' with DL BLER > {bler_threshold}")
    
    # This query finds the average performance for a specific slice and
    # checks if the average block error rate exceeds our congestion threshold.
    query = f"""
    SELECT
        slicing_id,
        AVG(dl_bler) as avg_dl_bler,
        AVG(dl_brate) as avg_dl_bitrate,
        COUNT(*) as num_samples
    FROM 
        analytics_ue_metrics
    WHERE
        slicing_id = '{slice_name}'
    GROUP BY
        slicing_id
    """
    
    try:
        query_results = run_athena_query(athena, query, DATABASE_NAME, S3_OUTPUT_LOCATION)
        
        if not query_results:
            response_body = {"is_congested": False, "details": "No data found for the specified slice."}
        else:
            slice_data = query_results[0]
            avg_bler = float(slice_data.get('avg_dl_bler', 0))
            
            if avg_bler > bler_threshold:
                response_body = {
                    "is_congested": True,
                    "congestion_level": avg_bler,
                    "details": f"Average Downlink BLER of {avg_bler:.2f} is above the threshold of {bler_threshold}.",
                    "avg_dl_bitrate": float(slice_data.get('avg_dl_bitrate', 0))
                }
            else:
                response_body = {
                    "is_congested": False,
                    "details": f"Average Downlink BLER of {avg_bler:.2f} is within acceptable limits.",
                    "congestion_level": avg_bler,
                    "avg_dl_bitrate": float(slice_data.get('avg_dl_bitrate', 0))
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
    test_event = {"slice_name": "slicing_1", "bler_threshold": 0.1}
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
