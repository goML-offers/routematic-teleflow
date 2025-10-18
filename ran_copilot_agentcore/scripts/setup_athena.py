import boto3
import time
from dotenv import load_dotenv

# --- Configuration ---
AWS_REGION = "ap-south-1"
S3_BUCKET_NAME = "ran-copilot-data-lake"
DATABASE_NAME = "ran_copilot_db"
S3_OUTPUT_LOCATION = f"s3://{S3_BUCKET_NAME}/athena-query-results/"

# Define the schema and location for each table
TABLES = {
    "analytics_ue_metrics": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/",
        "columns": [
            ("time", "string"), ("cc", "int"), ("pci", "int"), ("earfcn", "int"),
            ("rsrp", "float"), ("pl", "float"), ("cfo", "float"), ("dl_mcs", "int"),
            ("dl_snr", "float"), ("dl_turbo", "string"), ("dl_brate", "float"),
            ("dl_bler", "float"), ("ul_ta", "int"), ("ul_mcs", "int"),
            ("ul_buff", "int"), ("ul_brate", "float"), ("ul_bler", "float"),
            ("rf_o", "float"), ("rf_u", "float"), ("rf_l", "float"),
            ("is_attached", "boolean"), ("cluster_id", "string"),
            ("slicing_id", "string"), ("scheduling_id", "string"),
            ("reservation_id", "string"), ("ue_id", "string")
        ]
    },
    "recommendation_drive_test": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/",
        "columns": [
            ("Timestamp", "timestamp"), ("RSRP_Result", "float"), ("Cell_Identity", "int"),
            ("PCI", "int"), ("Band", "int"), ("DL_Freq", "int"), ("UL_Freq", "int"),
            ("DL_BW", "string"), ("UL_BW", "string"), ("TX_Power", "float"), ("Antenna_Gain", "float")
        ]
    },
    "forecasting_signal_metrics": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/",
        "columns": [
            ("Timestamp", "timestamp"), ("Locality", "string"), ("Latitude", "double"),
            ("Longitude", "double"), ("Signal_Strength_dBm", "float"),
            ("Signal_Quality_Percent", "float"), ("Data_Throughput_Mbps", "float"),
            ("Latency_ms", "float"), ("Network_Type", "string"),
            ("BB60C_Measurement_dBm", "float"), ("srsRAN_Measurement_dBm", "float"),
            ("BladeRFxA9_Measurement_dBm", "float")
        ]
    },
    "fault_management_alarms": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/",
        "columns": [
            ("Timestamp", "timestamp"), ("cell_id", "string"),
            ("alarm_name", "string"), ("severity", "string")
        ]
    },
    "cem_mos_scores": {
        "s3_location": f"s3://{S3_BUCKET_NAME}/",
        "columns": [
            ("Timestamp", "timestamp"), ("locality", "string"),
            ("mean_opinion_score", "float")
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
    
    # 2. Create the tables
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
