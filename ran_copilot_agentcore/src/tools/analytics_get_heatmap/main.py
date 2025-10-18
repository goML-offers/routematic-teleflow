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

def get_color_for_value(value, min_val, max_val):
    """Helper function to map a value to a color gradient (Green -> Yellow -> Red)."""
    # Normalize value to be between 0 and 1
    normalized = (value - min_val) / (max_val - min_val)
    
    # Invert for signal strength (lower is worse)
    normalized = 1 - normalized
    
    red = int(255 * min(1, normalized * 2))
    green = int(255 * min(1, (1 - normalized) * 2))
    
    return f"#{red:02x}{green:02x}00" # RRGGBB format

def handler(event, context):
    """
    This Lambda function queries Athena to get geo-located KPI data and formats
    it as a GeoJSON FeatureCollection for heatmap visualization.
    """
    load_dotenv()
    athena = boto3.client('athena', region_name=AWS_REGION)

    kpi_name = event.get('kpi_name', 'signal_strength_dbm') 
    
    print(f"AnalyticsTool Lambda: Generating heatmap data for KPI: {kpi_name}")
    
    query = f"""
    SELECT 
        longitude,
        latitude,
        "{kpi_name}" as value
    FROM 
        forecasting_signal_metrics
    WHERE 
        longitude IS NOT NULL 
        AND latitude IS NOT NULL
        AND "{kpi_name}" IS NOT NULL
    LIMIT 500 -- Limit for performance in this example
    """
    
    try:
        query_results = run_athena_query(athena, query, DATABASE_NAME, S3_OUTPUT_LOCATION)
        
        if not query_results:
            return {'statusCode': 200, 'body': json.dumps({"type": "FeatureCollection", "features": []})}

        # Convert results to GeoJSON Features
        features = []
        values = [float(r['value']) for r in query_results]
        min_val, max_val = min(values), max(values)

        for row in query_results:
            try:
                lon = float(row['longitude'])
                lat = float(row['latitude'])
                val = float(row['value'])
                
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "value": val,
                        "color": get_color_for_value(val, min_val, max_val)
                    }
                }
                features.append(feature)
            except (ValueError, TypeError):
                continue # Skip rows with invalid data

        geojson_response = {"type": "FeatureCollection", "features": features}
        
        return {
            'statusCode': 200,
            'body': json.dumps(geojson_response)
        }
    except Exception as e:
        print(f"Error executing query: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }

if __name__ == '__main__':
    test_event = {"kpi_name": "signal_strength_dbm"}
    response = handler(test_event, None)
    print("Lambda Response:")
    print(json.dumps(response, indent=2))
