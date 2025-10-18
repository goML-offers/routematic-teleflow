import os
import pandas as pd
import glob
import re
import numpy as np
from datetime import datetime, timedelta

def create_analytics_dataset(base_path, output_path):
    """
    Consolidates UE and eNodeB metrics from the neu_ms35v1320 dataset.
    This dataset is for the Analytics Agent.
    """
    print("Creating dataset for Analytics Agent...")
    # This function will be an expanded version of the previous script,
    # combining both ue_metrics.csv and enb_metrics.csv.
    # For brevity, we'll reuse the logic for ue_metrics for now.
    
    search_pattern = os.path.join(base_path, '**', 'ue_metrics.csv')
    ue_metrics_files = glob.glob(search_pattern, recursive=True)
    
    if not ue_metrics_files:
        print("No ue_metrics.csv files found for Analytics dataset.")
        return

    all_ue_data = []
    for file_path in ue_metrics_files:
        try:
            parts = re.split(r'[\\/]', file_path)
            dataset_kpm_index = parts.index('dataset-kpm')
            
            cluster_id = parts[dataset_kpm_index + 1]
            slicing_id = parts[dataset_kpm_index + 2]
            scheduling_id = parts[dataset_kpm_index + 3]
            reservation_id = parts[dataset_kpm_index + 4]
            ue_id = parts[dataset_kpm_index + 5].split('_')[1]

            df = pd.read_csv(file_path)
            df['cluster_id'] = cluster_id
            df['slicing_id'] = slicing_id
            df['scheduling_id'] = scheduling_id
            df['reservation_id'] = reservation_id
            df['ue_id'] = ue_id
            all_ue_data.append(df)
        except (ValueError, IndexError):
            continue
            
    if all_ue_data:
        consolidated_df = pd.concat(all_ue_data, ignore_index=True)
        consolidated_df.to_csv(output_path, index=False)
        print(f"Analytics dataset created at: {output_path}")

def create_recommendation_dataset(base_path, output_path):
    """
    Combines drive-test data with cell parameters for root cause analysis.
    This dataset is for the Recommendation Agent.
    """
    print("\nCreating dataset for Recommendation Agent...")
    try:
        # We will process one of the drive test runs as an example
        yaw_path = os.path.join(base_path, 'Dryad', 'yaw315')
        rsrp_path = os.path.join(yaw_path, 'inputf1_rsrp_with_header.csv')
        params_path = os.path.join(yaw_path, 'Serving_cell_Params_ENDC.csv')

        rsrp_df = pd.read_csv(rsrp_path)
        params_df = pd.read_csv(params_path)
        
        # For simplicity, we'll assume a single set of parameters applies
        # to all RSRP readings in this file. A real scenario might need a join.
        # We will append the first row of parameters to all rsrp readings.
        if not params_df.empty:
            params_series = params_df.iloc[0]
            for col, value in params_series.items():
                rsrp_df[col] = value
        
        rsrp_df.to_csv(output_path, index=False)
        print(f"Recommendation dataset created at: {output_path}")
    except FileNotFoundError as e:
        print(f"Could not create recommendation dataset. File not found: {e}")

def create_forecasting_dataset(base_path, output_path):
    """
    Prepares time-series data for forecasting traffic and load.
    This dataset is for the Forecasting Agent.
    """
    print("\nCreating dataset for Forecasting Agent...")
    try:
        signal_metrics_path = os.path.join(base_path, 'signal_metrics.csv')
        df = pd.read_csv(signal_metrics_path)
        
        # Basic cleaning: convert timestamp to datetime and sort
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp').reset_index(drop=True)
        
        df.to_csv(output_path, index=False)
        print(f"Forecasting dataset created at: {output_path}")
    except FileNotFoundError as e:
        print(f"Could not create forecasting dataset. File not found: {e}")

def create_fault_dataset(output_path, num_records=1000):
    """
    Generates a simulated dataset of historical network alarms.
    This dataset is for the Recommendation and Forecasting Agents.
    """
    print("\nCreating simulated dataset for Fault Management...")
    alarms = [
        "High_VSWR", "Link_Failure", "Power_Supply_Failure", 
        "High_Temperature", "Configuration_Mismatch", "Handover_Failure"
    ]
    severities = ["Critical", "Major", "Minor", "Warning"]
    cell_ids = [f"cell_{chr(65+i)}" for i in range(10)] # cell_A, cell_B, ...

    data = {
        "Timestamp": [datetime.now() - timedelta(hours=np.random.randint(0, 720)) for _ in range(num_records)],
        "cell_id": np.random.choice(cell_ids, num_records),
        "alarm_name": np.random.choice(alarms, num_records),
        "severity": np.random.choice(severities, num_records, p=[0.1, 0.3, 0.4, 0.2])
    }
    df = pd.DataFrame(data).sort_values('Timestamp').reset_index(drop=True)
    df.to_csv(output_path, index=False)
    print(f"Fault management dataset created at: {output_path}")

def create_cem_dataset(output_path, num_records=5000):
    """
    Generates a simulated dataset of subscriber experience (CEM) data.
    This dataset is for the Analytics Agent.
    """
    print("\nCreating simulated dataset for Customer Experience Management...")
    localities = ["Anisabad", "Fraser Road", "Boring Canal Road", "Danapur", "Phulwari Sharif"]
    
    data = {
        "Timestamp": [datetime.now() - timedelta(minutes=np.random.randint(0, 1440)) for _ in range(num_records)],
        "locality": np.random.choice(localities, num_records),
        "mean_opinion_score": np.random.uniform(1.0, 5.0, num_records).round(2)
    }
    df = pd.DataFrame(data).sort_values('Timestamp').reset_index(drop=True)
    df.to_csv(output_path, index=False)
    print(f"CEM dataset created at: {output_path}")


if __name__ == '__main__':
    # Get the absolute path to the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Build the path to the project root (one level up)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))

    # Define base paths using the absolute project root
    neu_dataset_path = os.path.join(project_root, 'datasets', 'neu_ms35v1320')
    ericsson_dataset_path = os.path.join(project_root, 'datasets', 'EricssionAMir')
    cellular_dataset_path = os.path.join(project_root, 'datasets', 'Cellular_Network_Analysis')
    
    # Create output directory
    output_dir = os.path.join(script_dir, 'curated_datasets')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Run all preprocessing functions
    create_analytics_dataset(neu_dataset_path, os.path.join(output_dir, 'analytics_ue_metrics.csv'))
    create_recommendation_dataset(ericsson_dataset_path, os.path.join(output_dir, 'recommendation_drive_test.csv'))
    create_forecasting_dataset(cellular_dataset_path, os.path.join(output_dir, 'forecasting_signal_metrics.csv'))
    create_fault_dataset(os.path.join(output_dir, 'fault_management_alarms.csv'))
    create_cem_dataset(os.path.join(output_dir, 'cem_mos_scores.csv'))
    
    print("\nAll datasets have been preprocessed and saved in the 'curated_datasets' directory.")
