import boto3
import time

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
        time.sleep(1)
        
    if status != 'SUCCEEDED':
        reason = stats['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
        raise Exception(f"Athena query failed: {reason}")
        
    print(f"Query executed successfully: {query_execution_id}")
    
    # Get results
    results_paginator = athena_client.get_paginator('get_query_results')
    results_iter = results_paginator.paginate(QueryExecutionId=query_execution_id)
    
    rows = []
    column_info = []
    
    first_page = True
    for page in results_iter:
        if first_page:
            column_info = [col['Name'] for col in page['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            first_page = False
            # Process rows from the first page (skip header row)
            for row in page['ResultSet']['Rows'][1:]:
                rows.append(dict(zip(column_info, [d.get('VarCharValue') for d in row['Data']])))
        else:
            # Process rows from subsequent pages
            for row in page['ResultSet']['Rows']:
                rows.append(dict(zip(column_info, [d.get('VarCharValue') for d in row['Data']])))
            
    return rows
