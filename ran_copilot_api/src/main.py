import os
import json
import logging
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sys
import random
from mangum import Mangum
from dotenv import load_dotenv
import uuid

# Add parent directory to path for imports
sys.path.insert(0, '/app')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="RAN Co-pilot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
athena_client = boto3.client('athena', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
bedrock_agent_client = boto3.client('bedrock-agentcore', region_name=os.getenv('AWS_REGION', 'ap-south-1'))

# Configuration from environment variables
ATHENA_DATABASE = os.getenv('ATHENA_DATABASE', 'ran_copilot')
ATHENA_OUTPUT_LOCATION = os.getenv('ATHENA_OUTPUT_LOCATION', 's3://ran-copilot-data-lake/athena-results/')
BEDROCK_AGENT_RUNTIME_ARN = os.getenv('BEDROCK_AGENT_RUNTIME_ARN') # e.g., 'arn:aws:bedrock-agentcore:...'

# Helper function for Athena
def run_athena_query(query: str) -> List[List[str]]:
    """Execute Athena query and return results as a list of lists."""
    try:
        logger.info(f"Running Athena query: {query}")
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': ATHENA_DATABASE},
            ResultConfiguration={'OutputLocation': ATHENA_OUTPUT_LOCATION}
        )
        query_id = response['QueryExecutionId']
        
        for _ in range(30): # 30 attempts, 1 sec sleep = 30 sec timeout
            result = athena_client.get_query_execution(QueryExecutionId=query_id)
            state = result['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            import time
            time.sleep(1)
        
        if state != 'SUCCEEDED':
            reason = result['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            raise Exception(f"Athena query failed: {reason}")
        
        results = athena_client.get_query_results(QueryExecutionId=query_id)
        
        data = []
        for row in results['ResultSet']['Rows'][1:]:  # Skip header
            values = [cell.get('VarCharValue', '') for cell in row['Data']]
            data.append(values)
        
        logger.info(f"Query returned {len(data)} rows")
        return data
    except Exception as e:
        logger.error(f"Athena query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

# ============================================================================
# API Models
# ============================================================================

class PingResponse(BaseModel):
    status: str
    timestamp: str

class DashboardKPI(BaseModel):
    rrc_success_rate: float
    active_cells: int
    critical_alarms: int
    network_load: float
    status: str

class CellStatus(BaseModel):
    cell_id: str
    latitude: float
    longitude: float
    status: str
    load_percentage: float
    rrc_success_rate: float

class TimeSeriesData(BaseModel):
    timestamp: str
    rrc_success_rate: float
    handover_success_rate: float
    throughput_mbps: float

class CellPerformance(BaseModel):
    cell_id: str
    rrc_success_rate: float
    handover_success_rate: float
    network_load: float
    active_alarms: int
    status: str

class AgentInvokeRequest(BaseModel):
    prompt: str
    sessionId: Optional[str] = None

class AgentInvokeResponse(BaseModel):
    completion: str
    sessionId: str

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/ping", response_model=PingResponse)
async def ping():
    """Health check endpoint"""
    return PingResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/api/dashboard/kpis", response_model=DashboardKPI)
async def get_dashboard_kpis():
    """Get dashboard KPIs from Athena, calculated over the entire dataset."""
    try:
        query = """
        SELECT 
            AVG(rrc_success_rate),
            COUNT(DISTINCT cell_id),
            SUM(CASE WHEN alarm_severity='CRITICAL' THEN 1 ELSE 0 END),
            AVG(network_load)
        FROM analytics_ue_metrics
        """
        results = run_athena_query(query)
        
        if not results:
            raise HTTPException(status_code=404, detail="No dashboard data available")
        
        row = results[0]
        rrc_rate = float(row[0]) if row[0] else 0.0
        active_cells = int(row[1]) if row[1] else 0
        critical_alarms = int(row[2]) if row[2] else 0
        network_load = float(row[3]) if row[3] else 0.0
        
        status = "Operational"
        if critical_alarms > 10 or network_load > 85: status = "Critical"
        elif rrc_rate < 90 or network_load > 60: status = "Degraded"
        
        return DashboardKPI(
            rrc_success_rate=rrc_rate,
            active_cells=active_cells,
            critical_alarms=critical_alarms,
            network_load=network_load,
            status=status
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
        if isinstance(e, HTTPException): raise
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cells/status", response_model=List[CellStatus])
async def get_cells_status():
    """Get cell status and location data from Athena."""
    try:
        # This query now fetches metrics only for cells that have coordinate data.
        query = """
        SELECT 
            cell_id, latitude, longitude,
            CASE
                WHEN AVG(rrc_success_rate) > 94.5 THEN 'Optimal'
                WHEN AVG(rrc_success_rate) > 93.5 THEN 'Degraded'
                ELSE 'Critical'
            END as status,
            AVG(network_load),
            AVG(rrc_success_rate)
        FROM analytics_ue_metrics
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY cell_id, latitude, longitude
        LIMIT 100
        """
        results = run_athena_query(query)
        
        return [
            CellStatus(
                cell_id=row[0],
                latitude=float(row[1]),
                longitude=float(row[2]),
                status=row[3],
                load_percentage=float(row[4]) if row[4] else 0,
                rrc_success_rate=float(row[5]) if row[5] else 0
            ) for row in results
        ]
    except Exception as e:
        logger.error(f"Error fetching cell status: {e}", exc_info=True)
        if isinstance(e, HTTPException): raise
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cells/performance", response_model=List[CellPerformance])
async def get_cell_performance(
    limit: int = Query(100, description="The maximum number of cells to return."),
    hours: int = Query(24, description="The time window in hours to calculate performance over.")
):
    """Get a ranked list of cell performance metrics from Athena."""
    try:
        query = f"""
        SELECT 
            cell_id,
            AVG(rrc_success_rate),
            AVG(handover_success_rate),
            AVG(network_load),
            SUM(CASE WHEN alarm_severity = 'CRITICAL' THEN 1 ELSE 0 END) as active_alarms,
            CASE 
                WHEN AVG(rrc_success_rate) > 94.5 THEN 'Optimal'
                WHEN AVG(rrc_success_rate) > 93.5 THEN 'Degraded'
                ELSE 'Critical'
            END as status
        FROM analytics_ue_metrics
        WHERE
            date_parse(time, '%Y-%m-%d %H:%i:%s.%f') >= ((SELECT MAX(date_parse(time, '%Y-%m-%d %H:%i:%s.%f')) FROM analytics_ue_metrics) - interval '{hours}' hour)
        GROUP BY cell_id
        ORDER BY AVG(rrc_success_rate) ASC
        LIMIT {limit}
        """
        results = run_athena_query(query)
        
        return [
            CellPerformance(
                cell_id=row[0],
                rrc_success_rate=float(row[1]) if row[1] else 0,
                handover_success_rate=float(row[2]) if row[2] else 0,
                network_load=float(row[3]) if row[3] else 0,
                active_alarms=int(float(row[4])) if row[4] else 0,
                status=row[5]
            ) for row in results
        ]
    except Exception as e:
        logger.error(f"Error fetching cell performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/timeseries", response_model=List[TimeSeriesData])
async def get_timeseries_analytics(hours: int = Query(24, description="Number of hours of data to fetch")) -> List[TimeSeriesData]:
    """Get time-series analytics data from Athena."""
    try:
        # The 'time' column is a string, so we must parse it into a timestamp for date functions.
        query = f"""
        SELECT
            date_trunc('hour', date_parse(time, '%Y-%m-%d %H:%i:%s.%f')) AS timestamp_hour,
            AVG(rrc_success_rate),
            AVG(handover_success_rate),
            AVG(throughput_mbps)
        FROM 
            analytics_ue_metrics
        WHERE 
            date_parse(time, '%Y-%m-%d %H:%i:%s.%f') >= ((SELECT MAX(date_parse(time, '%Y-%m-%d %H:%i:%s.%f')) FROM analytics_ue_metrics) - interval '{hours}' hour)
        GROUP BY 
            1
        ORDER BY 
            1 ASC
        """
        results = run_athena_query(query)
        
        # Format the results into the Pydantic model
        return [
            TimeSeriesData(
                timestamp=row[0],
                rrc_success_rate=float(row[1]) if row[1] else 0,
                handover_success_rate=float(row[2]) if row[2] else 0,
                throughput_mbps=float(row[3]) if row[3] else 0
            ) for row in results
        ]
    except Exception as e:
        logger.error(f"Error fetching time-series analytics: {e}", exc_info=True)
        if isinstance(e, HTTPException): raise
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kpi/heatmap")
async def get_kpi_heatmap_data(kpi_name: str = "throughput_mbps"):
    """Generates geographic heatmap data for a given KPI."""
    try:
        query = f"""
        SELECT
            latitude,
            longitude,
            AVG({kpi_name}) as avg_kpi_value
        FROM analytics_ue_metrics
        WHERE
            latitude IS NOT NULL AND longitude IS NOT NULL
        GROUP BY latitude, longitude
        LIMIT 500
        """
        results = run_athena_query(query)
        
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row[1]), float(row[0])]
                },
                "properties": {"kpi_value": float(row[2]) if row[2] else 0}
            }
            for row in results if row[0] and row[1]
        ]
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}", exc_info=True)
        if isinstance(e, HTTPException): raise
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/invoke", response_model=AgentInvokeResponse)
async def agent_invoke(request: AgentInvokeRequest):
    """Invokes the Bedrock agent."""
    logger.info("--- Agent Invocation Start ---")
    logger.info(f"Received prompt: {request.prompt}")
    logger.info(f"Received sessionId: {request.sessionId}")

    # Log the environment variables to ensure they are loaded correctly
    logger.info(f"Using BEDROCK_AGENT_RUNTIME_ARN: {BEDROCK_AGENT_RUNTIME_ARN}")

    if not BEDROCK_AGENT_RUNTIME_ARN:
        logger.error("Bedrock Agent Runtime ARN not configured.")
        raise HTTPException(
            status_code=500, 
            detail="Bedrock Agent not configured. Please set BEDROCK_AGENT_RUNTIME_ARN environment variable."
        )

    # Session ID must be >= 33 characters for bedrock-agentcore
    session_id = request.sessionId or (str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', '')[:1])
    logger.info(f"Using session_id: {session_id}")
    
    try:
        payload = json.dumps({
            "input": {"prompt": request.prompt}
        })

        logger.info("Calling bedrock_agent_client.invoke_agent_runtime...")
        response = bedrock_agent_client.invoke_agent_runtime(
            agentRuntimeArn=BEDROCK_AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT"  # Assuming default qualifier
        )
        logger.info("Bedrock API call successful. Processing response.")

        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        # The actual agent output seems to be nested. Adjust based on actual response structure.
        # This is a guess based on the previous agent's structure.
        completion = response_data.get("output", {}).get("message", {}).get("content", "No content found")

        logger.info(f"Agent completion: {completion}")
        logger.info("--- Agent Invocation End ---")
        return AgentInvokeResponse(
            completion=completion,
            sessionId=session_id
        )
    except Exception as e:
        logger.error(f"Bedrock Agent invocation error: {e}", exc_info=True)
        logger.info("--- Agent Invocation End (with error) ---")
        raise HTTPException(status_code=500, detail=f"Failed to invoke agent: {e}")

# Add Mangum handler for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    # Make sure to set environment variables for BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID
    # For local testing, you can create a .env file.
    logger.info("Starting Uvicorn server.")
    uvicorn.run(app, host="0.0.0.0", port=8080)
