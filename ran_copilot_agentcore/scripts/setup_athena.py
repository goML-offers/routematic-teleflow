import boto3
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# It's recommended to use environment variables for these settings
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'ran-copilot-data-lake')
DATABASE_NAME = 'ran_copilot'
ATHENA_OUTPUT_LOCATION = f's3://{S3_BUCKET_NAME}/athena-results/'

# Initialize AWS Athena client
athena_client = boto3.client('athena', region_name=AWS_REGION)

def execute_athena_query(query: str, database: str = DATABASE_NAME):
    """
    Executes a given DDL query in Athena and waits for it to succeed.
    """
    print(f"Executing Query: {query[:80]}...")
    try:
        # Prepare arguments for start_query_execution
        query_args = {
            'QueryString': query,
            'ResultConfiguration': {'OutputLocation': ATHENA_OUTPUT_LOCATION}
        }
        if database:
            query_args['QueryExecutionContext'] = {'Database': database}

        response = athena_client.start_query_execution(**query_args)
        query_id = response['QueryExecutionId']
        
        # Wait for the query to complete
        while True:
            status = athena_client.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                if state == 'FAILED':
                    reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                    print(f"Query Failed! Reason: {reason}")
                    raise Exception(f"Athena query failed: {reason}")
                break
            time.sleep(2)
        print("Query Succeeded.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def setup_database_and_tables():
    """
    Sets up the Athena database and all required tables.
    """
    print("--- Starting Athena Setup ---")
    
    # --- Create Database if not exists ---
    create_database_query = f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME};"
    try:
        # Note: calling with database=None to omit QueryExecutionContext
        execute_athena_query(create_database_query, database=None)
        print(f"Database '{DATABASE_NAME}' created or already exists.")
    except Exception as e:
        print(f"Could not create database. Setup cannot continue. Error: {e}")
        return

    # --- Table: analytics_ue_metrics ---
    execute_athena_query(f'DROP TABLE IF EXISTS {DATABASE_NAME}.analytics_ue_metrics')
    create_ue_metrics_table = f"""
    CREATE EXTERNAL TABLE {DATABASE_NAME}.analytics_ue_metrics (
        `time` string,
        `cell_id` string,
        `rrc_success_rate` double,
        `handover_success_rate` double,
        `throughput_mbps` double,
        `network_load` double,
        `active_alarms` int,
        `alarm_severity` string,
        `latitude` double,
        `longitude` double
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES ('separatorChar' = ',')
    LOCATION 's3://{S3_BUCKET_NAME}/analytics_ue_metrics/'
    TBLPROPERTIES ('skip.header.line.count'='1', 'use.null.for.invalid.data'='true');
    """
    execute_athena_query(create_ue_metrics_table)
    print("Table 'analytics_ue_metrics' created successfully.")

    # --- Table: analytics_alarms ---
    execute_athena_query(f'DROP TABLE IF EXISTS {DATABASE_NAME}.analytics_alarms')
    create_alarms_table = f"""
    CREATE EXTERNAL TABLE {DATABASE_NAME}.analytics_alarms (
        `time` timestamp,
        `cell_id` string,
        `alarm_name` string,
        `alarm_severity` string
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES ('separatorChar' = ',')
    LOCATION 's3://{S3_BUCKET_NAME}/analytics_alarms/'
    TBLPROPERTIES ('skip.header.line.count'='1', 'use.null.for.invalid.data'='true');
    """
    execute_athena_query(create_alarms_table)
    print("Table 'analytics_alarms' created successfully.")
    
    # --- Table: analytics_config_changes ---
    execute_athena_query(f'DROP TABLE IF EXISTS {DATABASE_NAME}.analytics_config_changes')
    create_config_changes_table = f"""
    CREATE EXTERNAL TABLE {DATABASE_NAME}.analytics_config_changes (
        `time` timestamp,
        `cell_id` string,
        `parameter_name` string,
        `old_value` string,
        `new_value` string
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES ('separatorChar' = ',')
    LOCATION 's3://{S3_BUCKET_NAME}/analytics_config_changes/'
    TBLPROPERTIES ('skip.header.line.count'='1', 'use.null.for.invalid.data'='true');
    """
    execute_athena_query(create_config_changes_table)
    print("Table 'analytics_config_changes' created successfully.")

    # --- Table: analytics_cem_metrics ---
    execute_athena_query(f'DROP TABLE IF EXISTS {DATABASE_NAME}.analytics_cem_metrics')
    create_cem_metrics_table = f"""
    CREATE EXTERNAL TABLE {DATABASE_NAME}.analytics_cem_metrics (
        `timestamp` timestamp,
        `cell_id` string,
        `satisfaction_score` double,
        `rrc_success_rate` double,
        `handover_success_rate` double,
        `throughput_mbps` double,
        `network_load` double
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES ('separatorChar' = ',')
    LOCATION 's3://{S3_BUCKET_NAME}/analytics_cem_metrics/'
    TBLPROPERTIES ('skip.header.line.count'='1', 'use.null.for.invalid.data'='true');
    """
    execute_athena_query(create_cem_metrics_table)
    print("Table 'analytics_cem_metrics' created successfully.")

    # --- Table: analytics_slice_metrics ---
    execute_athena_query(f'DROP TABLE IF EXISTS {DATABASE_NAME}.analytics_slice_metrics')
    create_slice_metrics_table = f"""
    CREATE EXTERNAL TABLE {DATABASE_NAME}.analytics_slice_metrics (
        `timestamp` timestamp,
        `slice_id` string,
        `prb_utilization` double,
        `throughput_mbps` double
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES ('separatorChar' = ',')
    LOCATION 's3://{S3_BUCKET_NAME}/analytics_slice_metrics/'
    TBLPROPERTIES ('skip.header.line.count'='1', 'use.null.for.invalid.data'='true');
    """
    execute_athena_query(create_slice_metrics_table)
    print("Table 'analytics_slice_metrics' created successfully.")

if __name__ == '__main__':
    setup_database_and_tables()