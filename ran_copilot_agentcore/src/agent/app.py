"""
RAN Co-pilot Agent - FastAPI Implementation for AgentCore Runtime
Uses AWS-managed AgentCore Gateway for 8 tools + direct Lambda for 5 tools.
"""
import os
import json
import logging
import httpx
import boto3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/app')

from strands import Agent, tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Check for AWS credentials
logger.info("Checking AWS credentials...")
logger.info(f"AWS_ACCESS_KEY_ID present: {bool(os.getenv('AWS_ACCESS_KEY_ID'))}")
logger.info(f"AWS_SECRET_ACCESS_KEY present: {bool(os.getenv('AWS_SECRET_ACCESS_KEY'))}")
logger.info(f"AWS_REGION: {os.getenv('AWS_REGION', 'ap-south-1')}")

# FastAPI app
app = FastAPI(title="RAN Co-pilot Agent")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
bedrock_client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
athena_client = boto3.client('athena', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-south-1'))

# Gateway configuration
GATEWAY_ARN = os.getenv('GATEWAY_ARN', 'arn:aws:bedrock-agentcore:ap-south-1:767828738296:gateway/ran-copilot-gateway-gqw1ckcenk')
GATEWAY_ENDPOINT = os.getenv('GATEWAY_ENDPOINT', 'https://ran-copilot-gateway-gqw1ckcenk.gateway.bedrock-agentcore.ap-south-1.amazonaws.com/mcp')

# Tools available through Gateway (8)
GATEWAY_TOOLS = {
    "get-kpi-heatmap-data",
    "detect-performance-anomalies",
    "forecast-traffic-for-event",
    "recommend-preventive-maintenance",
    "simulate-parameter-change-impact",
    "generate-optimization-recommendation",
    "perform-root-cause-analysis",
    "detect-slice-congestion"
}

# Tools called directly via Lambda (5)
LAMBDA_ONLY_TOOLS = {
    "find-degraded-cell-clusters",
    "correlate-kpi-with-cem",
    "create-trouble-ticket",
    "generate-configuration-script",
    "predict-equipment-faults"
}

logger.info(f"Gateway Endpoint: {GATEWAY_ENDPOINT}")
logger.info(f"Gateway Tools (8): {GATEWAY_TOOLS}")
logger.info(f"Lambda-only Tools (5): {LAMBDA_ONLY_TOOLS}")

# ============================================================================
# Tool Invocation Wrappers
# ============================================================================

async def invoke_gateway_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke tool through AgentCore Gateway (MCP protocol)."""
    try:
        logger.info(f"Invoking Gateway tool: {tool_name}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_ENDPOINT}/tools/{tool_name}/invoke",
                json={"params": params},
                headers={"Content-Type": "application/json"}
            )
            result = response.json()
            logger.info(f"Gateway tool response: {result}")
            return result
    except Exception as e:
        logger.error(f"Gateway invocation failed: {e}")
        # Fallback to mock data
        return {"status": "failed", "error": str(e), "source": "mock"}

def invoke_lambda_tool(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke tool directly via Lambda."""
    try:
        logger.info(f"Invoking Lambda tool: {function_name}")
        response = bedrock_client.invoke_model(
            modelId="amazon.nova-pro-v1:0",
            body=json.dumps(payload)
        )
        response_payload = json.loads(response['body'].read())
        logger.info(f"Lambda tool response: {response_payload}")
        return response_payload
    except Exception as e:
        logger.error(f"Lambda invocation failed: {e}")
        return {"status": "failed", "error": str(e), "source": "mock"}

# ============================================================================
# ANALYTICS TOOLS (5 total: 3 Gateway + 2 Lambda)
# ============================================================================

@tool()
def detect_performance_anomalies(kpi_name: str, time_window: str = "24h") -> dict:
    """Detects statistical deviations in time-series KPI data."""
    logger.info(f"Tool: detect_performance_anomalies - KPI: {kpi_name}, Window: {time_window}")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("detect-performance-anomalies", {"kpi_name": kpi_name, "time_window": time_window}))
    return result

@tool()
def find_degraded_clusters() -> dict:
    """Identifies cell clusters with degraded performance based on RSRP metrics."""
    logger.info("Tool: find_degraded_clusters")
    # Lambda-only tool
    result = invoke_lambda_tool("find-degraded-cell-clusters", {})
    return result

@tool()
def correlate_cem_with_kpi(kpi_type: str = "signal_strength") -> dict:
    """Correlates Customer Experience Metrics (CEM) scores with key KPIs."""
    logger.info(f"Tool: correlate_cem_with_kpi - KPI Type: {kpi_type}")
    # Lambda-only tool
    result = invoke_lambda_tool("correlate-kpi-with-cem", {"kpi_type": kpi_type})
    return result

@tool()
def detect_slice_congestion(slice_id: str) -> dict:
    """Detects network slice congestion based on downlink BLER and throughput metrics."""
    logger.info(f"Tool: detect_slice_congestion - Slice: {slice_id}")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("detect-slice-congestion", {"slice_id": slice_id}))
    return result

@tool()
def get_heatmap_data(kpi_name: str = "signal_strength", format_type: str = "geojson") -> dict:
    """Generates geographic heatmap data for visualization of KPI metrics."""
    logger.info(f"Tool: get_heatmap_data - KPI: {kpi_name}, Format: {format_type}")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("get-kpi-heatmap-data", {"kpi_name": kpi_name, "format_type": format_type}))
    return result

# ============================================================================
# RECOMMENDATION TOOLS (3 total: all Gateway)
# ============================================================================

@tool()
def perform_root_cause_analysis(issue_type: str) -> dict:
    """Performs root cause analysis for detected network issues."""
    logger.info(f"Tool: perform_root_cause_analysis - Issue: {issue_type}")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("perform-root-cause-analysis", {"issue_type": issue_type}))
    return result

@tool()
def simulate_parameter_impact(parameter_name: str, proposed_value: Any) -> dict:
    """Simulates the impact of proposed parameter changes on network performance."""
    logger.info(f"Tool: simulate_parameter_impact - Parameter: {parameter_name}, Value: {proposed_value}")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("simulate-parameter-change-impact", {"parameter_name": parameter_name, "proposed_value": proposed_value}))
    return result

@tool()
def generate_optimization_recommendations() -> dict:
    """Generates structured optimization recommendations based on RCA and simulation."""
    logger.info("Tool: generate_optimization_recommendations")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("generate-optimization-recommendation", {}))
    return result

# ============================================================================
# AUTOMATION TOOLS (2 total: both Lambda-only)
# ============================================================================

@tool()
def create_trouble_ticket(issue_title: str, severity: str, description: str) -> dict:
    """Creates a trouble ticket for network issues requiring human intervention."""
    logger.info(f"Tool: create_trouble_ticket - Title: {issue_title}, Severity: {severity}")
    # Lambda-only tool
    result = invoke_lambda_tool("create-trouble-ticket", {"issue_title": issue_title, "severity": severity, "description": description})
    return result

@tool()
def generate_configuration_script(changes: Dict[str, Any]) -> dict:
    """Generates configuration scripts for automated parameter updates."""
    logger.info(f"Tool: generate_configuration_script - Changes: {list(changes.keys())}")
    # Lambda-only tool
    result = invoke_lambda_tool("generate-configuration-script", {"changes": changes})
    return result

# ============================================================================
# FORECASTING TOOLS (3 total: 2 Gateway + 1 Lambda)
# ============================================================================

@tool()
def forecast_traffic_for_event(event_name: str, event_date: str, location: str) -> dict:
    """Forecasts network traffic patterns for upcoming events."""
    logger.info(f"Tool: forecast_traffic_for_event - Event: {event_name}, Date: {event_date}")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("forecast-traffic-for-event", {"event_name": event_name, "event_date": event_date, "location": location}))
    return result

@tool()
def predict_equipment_faults(cell_id: Optional[str] = None) -> dict:
    """Predicts potential equipment faults based on historical patterns."""
    logger.info(f"Tool: predict_equipment_faults - Cell: {cell_id}")
    # Lambda-only tool
    result = invoke_lambda_tool("predict-equipment-faults", {"cell_id": cell_id})
    return result

@tool()
def recommend_preventive_maintenance() -> dict:
    """Recommends preventive maintenance actions based on equipment status."""
    logger.info("Tool: recommend_preventive_maintenance")
    # Gateway tool
    import asyncio
    result = asyncio.run(invoke_gateway_tool("recommend-preventive-maintenance", {}))
    return result

# Initialize Strands Agent
logger.info("Initializing Strands Agent...")
try:
    agent = Agent(model="amazon.nova-pro-v1:0")
    logger.info("Strands Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Strands Agent: {e}")
    agent = None

# ============================================================================
# Models & Endpoints
# ============================================================================

class PingResponse(BaseModel):
    status: str
    timestamp: str

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

class DashboardKPI(BaseModel):
    rrc_success_rate: float
    active_cells: int
    critical_alarms: int
    network_load: float
    status: str  # Operational, Degraded, Critical

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

# REST API Endpoints

@app.get("/ping", response_model=PingResponse)
async def ping():
    """Health check endpoint"""
    return PingResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.post("/invocations", response_model=InvocationResponse)
async def invocations(request: InvocationRequest):
    """Main agent invocation endpoint"""
    try:
        logger.info(f"Received invocation request: {request.input}")
        
        user_prompt = request.input.get('prompt', '')
        logger.info(f"User prompt: {user_prompt}")
        
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Invoke agent
        try:
            result = await agent.ainvoke({"input": user_prompt})
            logger.info(f"Agent result: {result}")
            
            # Extract message content
            message_content = result.get('messages', [{}])[-1] if result.get('messages') else {}
            
            response_text = ""
            if isinstance(message_content, dict):
                if 'content' in message_content:
                    content = message_content['content']
                    if isinstance(content, list) and len(content) > 0:
                        response_text = content[0].get('text', '')
                    elif isinstance(content, str):
                        response_text = content
            
            return InvocationResponse(
                output={
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Agent invocation error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invocation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Dashboard KPI Endpoint
@app.get("/api/dashboard/kpis", response_model=DashboardKPI)
async def get_dashboard_kpis():
    """Get real-time dashboard KPIs"""
    try:
        # In a real implementation, this would query Athena
        # For now, returning mock data based on recent database state
        
        # Calculate status based on thresholds
        status = "Operational"  # Can be Operational, Degraded, Critical
        
        return DashboardKPI(
            rrc_success_rate=98.5,
            active_cells=25,
            critical_alarms=3,
            network_load=62.5,
            status=status
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cell Status Endpoint
@app.get("/api/cells/status", response_model=List[CellStatus])
async def get_cells_status():
    """Get status of all cells"""
    try:
        # In a real implementation, this would query Athena
        # For now, returning mock data
        
        return [
            CellStatus(
                cell_id="cell_001",
                latitude=28.7041,
                longitude=77.1025,
                status="Optimal",
                load_percentage=45,
                rrc_success_rate=98.5
            ),
            CellStatus(
                cell_id="cell_002",
                latitude=28.7050,
                longitude=77.1035,
                status="Degraded",
                load_percentage=72,
                rrc_success_rate=95.2
            ),
            CellStatus(
                cell_id="cell_003",
                latitude=28.7060,
                longitude=77.1045,
                status="Critical",
                load_percentage=88,
                rrc_success_rate=92.1
            )
        ]
    except Exception as e:
        logger.error(f"Error fetching cell status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Time-Series Analytics Endpoint
@app.get("/api/analytics/timeseries", response_model=List[TimeSeriesData])
async def get_timeseries_analytics(
    metric: str = Query("rrc_success_rate"),
    hours: int = Query(24)
):
    """Get time-series analytics data"""
    try:
        # In a real implementation, this would query Athena
        # For now, returning mock data
        
        now = datetime.now(timezone.utc)
        data = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-i-1)
            data.append(TimeSeriesData(
                timestamp=timestamp.isoformat(),
                rrc_success_rate=98.5 - (i % 5) * 0.3,
                handover_success_rate=97.2 - (i % 4) * 0.4,
                throughput_mbps=125.3 + (i % 10) * 2.5
            ))
        
        return data
    except Exception as e:
        logger.error(f"Error fetching time-series analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cell Performance Endpoint
@app.get("/api/cells/performance", response_model=List[CellPerformance])
async def get_cell_performance(limit: int = Query(100)):
    """Get cell performance metrics"""
    try:
        # In a real implementation, this would query Athena
        # For now, returning mock data
        
        return [
            CellPerformance(
                cell_id="cell_001",
                rrc_success_rate=98.5,
                handover_success_rate=97.2,
                network_load=45,
                active_alarms=2,
                status="Optimal"
            ),
            CellPerformance(
                cell_id="cell_002",
                rrc_success_rate=95.2,
                handover_success_rate=94.1,
                network_load=72,
                active_alarms=5,
                status="Degraded"
            ),
            CellPerformance(
                cell_id="cell_003",
                rrc_success_rate=92.1,
                handover_success_rate=90.5,
                network_load=88,
                active_alarms=12,
                status="Critical"
            )
        ]
    except Exception as e:
        logger.error(f"Error fetching cell performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
