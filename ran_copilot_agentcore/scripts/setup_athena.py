import boto3
import time
from dotenv import load_dotenv

# --- Configuration ---
AWS_REGION = "ap-south-1"
S3_BUCKET_NAME = "ran-copilot-data-lake"
DATABASE_NAME = "ran_copilot"
S3_OUTPUT_LOCATION = f"s3://{S3_BUCKET_NAME}/athena-query-results/"

# Define the schema and location for each table
TABLES = {
    "analytics_ue_metrics": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/ue_metrics/",
        "columns": [
            ("time", "timestamp"),
            ("cell_id", "string"),
            ("rrc_success_rate", "float"),
            ("handover_success_rate", "float"),
            ("throughput_mbps", "float"),
            ("network_load", "float"),
            ("active_alarms", "int"),
            ("alarm_severity", "string"),
            ("latitude", "double"),
            ("longitude", "double")
        ]
    },
    "analytics_alarms": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/alarms/",
        "columns": [
            ("time", "timestamp"),
            ("cell_id", "string"),
            ("alarm_name", "string"),
            ("alarm_severity", "string")
        ]
    },
    "analytics_config_changes": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/config_changes/",
        "columns": [
            ("time", "timestamp"),
            ("cell_id", "string"),
            ("parameter_name", "string"),
            ("old_value", "string"),
            ("new_value", "string")
        ]
    },
    "analytics_cem_metrics": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/cem/",
        "columns": [
            ("timestamp", "timestamp"),
            ("satisfaction_score", "float")
        ]
    },
    "analytics_slice_metrics": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/slices/",
        "columns": [
            ("timestamp", "timestamp"),
            ("slice_id", "string"),
            ("prb_utilization", "float"),
            ("throughput_mbps", "float")
        ]
    },
    "analytics_events_metadata": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/events_metadata/",
        "columns": [
            ("event_id", "string"),
            ("event_name", "string"),
            ("event_type", "string"),
            ("event_date", "timestamp")
        ]
    },
    "analytics_hourly_event_traffic": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/processed-data/event_traffic/",
        "columns": [
            ("event_id", "string"),
            ("hour_of_day", "int"),
            ("total_traffic_gb", "float")
        ]
    }
}

def run_athena_query(athena_client, query, database, s3_output):
    """Executes an Athena query and waits for it to complete."""
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': s3_output}
    )
    query_execution_id = response['QueryExecutionId']
    
    while True:
        stats = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = stats['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1) # Poll every second
        
    if status != 'SUCCEEDED':
        raise Exception(f"Athena query failed: {stats['QueryExecution']['Status']['StateChangeReason']}")
        
    print(f"Query executed successfully: {query_execution_id}")

def main():
    """Main function to set up the Athena database and tables."""
    # Load environment variables from .env file
    load_dotenv()
    
    athena = boto3.client('athena', region_name=AWS_REGION)

    # 1. Create the database
    print(f"Creating database: {DATABASE_NAME}")
    create_db_query = f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME};"
    # For CREATE DATABASE, we don't need to specify a database in the context
    response = athena.start_query_execution(
        QueryString=create_db_query,
        ResultConfiguration={'OutputLocation': S3_OUTPUT_LOCATION}
    )
    # A simple wait, as this query is usually fast
    time.sleep(3) 
    print("Database created or already exists.")
    
    # 2. Drop existing tables to ensure a clean slate with the new schema
    for table_name in TABLES.keys():
        print(f"Dropping table if it exists: {table_name}")
        drop_query = f"DROP TABLE IF EXISTS {DATABASE_NAME}.{table_name};"
        try:
            # We run drop queries without the wait logic for simplicity
            athena.start_query_execution(
                QueryString=drop_query,
                QueryExecutionContext={'Database': DATABASE_NAME},
                ResultConfiguration={'OutputLocation': S3_OUTPUT_LOCATION}
            )
            time.sleep(2) # Give it a moment to process
        except Exception as e:
            print(f"Could not drop table {table_name}, it might not exist. Error: {e}")

    # 3. Create the tables with the new, correct schema
    for table_name, config in TABLES.items():
        print(f"\nCreating table: {table_name}")
        
        cols_sql = ", ".join([f"`{col[0]}` {col[1]}" for col in config["columns"]])
        
        create_table_query = f"""
        CREATE EXTERNAL TABLE {DATABASE_NAME}.{table_name} (
          {cols_sql}
        )
        ROW FORMAT DELIMITED
          FIELDS TERMINATED BY ','
        LOCATION '{config["s3_location"]}'
        TBLPROPERTIES (
          'skip.header.line.count'='1',
          'areColumnsQuoted'='false'
        );
        """
        
        try:
            run_athena_query(athena, create_table_query, DATABASE_NAME, S3_OUTPUT_LOCATION)
            print(f"Table '{table_name}' created successfully.")
        except Exception as e:
            print(f"Error creating table '{table_name}': {e}")

if __name__ == '__main__':
    main()
