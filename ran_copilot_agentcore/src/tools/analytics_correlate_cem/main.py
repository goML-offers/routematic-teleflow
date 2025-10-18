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
    This Lambda function finds correlations between network KPIs and CEM scores.
    For this implementation, we will find the average network KPIs in locations
    with a low Mean Opinion Score (MOS).
    """
    load_dotenv()
    athena = boto3.client('athena', region_name=AWS_REGION)

    mos_threshold = event.get('mos_threshold', 2.5) 
    
    print(f"AnalyticsTool Lambda: Correlating KPIs with CEM scores below {mos_threshold} MOS")
    
    # This query joins our forecasting/signal data with our simulated CEM data
    # to find the average KPIs in areas where user experience was poor.
    query = f"""
    SELECT
        cem.locality,
        COUNT(*) AS num_low_mos_samples,
        AVG(sig.signal_strength_dbm) AS avg_rsrp_in_low_mos_areas,
        AVG(sig.latency_ms) AS avg_latency_in_low_mos_areas,
        AVG(sig.data_throughput_mbps) AS avg_throughput_in_low_mos_areas
    FROM 
        cem_mos_scores cem
    JOIN 
        forecasting_signal_metrics sig ON cem.locality = sig.locality
    WHERE
        cem.mean_opinion_score < {mos_threshold}
    GROUP BY
        cem.locality
    ORDER BY
        num_low_mos_samples DESC
    LIMIT 10;
    """
    
    try:
        query_results = run_athena_query(athena, query, DATABASE_NAME, S3_OUTPUT_LOCATION)
        
        response_body = {"kpi_correlations_with_low_cem": query_results}
        
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
    test_event = {"mos_threshold": 2.5}
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
