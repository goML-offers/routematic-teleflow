"""
RAN Co-pilot Agent - FastAPI Implementation for AgentCore Runtime
Uses AWS-managed AgentCore Gateway for 8 tools + direct Lambda for 5 tools.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import logging
import boto3
import os
import httpx

from strands import Agent, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="RAN Co-pilot Agent", version="1.0.0")

# Initialize AWS Lambda client
lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'ap-south-1'))

# ============================================================================
# Gateway Configuration
# ============================================================================

GATEWAY_ARN = "arn:aws:bedrock-agentcore:ap-south-1:767828738296:gateway/ran-copilot-gateway-gqw1ckcenk"
GATEWAY_ENDPOINT = "https://ran-copilot-gateway-gqw1ckcenk.gateway.bedrock-agentcore.ap-south-1.amazonaws.com/mcp"

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
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response['Payload'].read())
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

# Initialize Strands Agent with all 13 tools
logger.info("Initializing Strands Agent with 13 tools (8 Gateway + 5 Lambda)...")
try:
    strands_agent = Agent(
        system_prompt="""You are an intelligent RAN Co-pilot assistant for Radio Access Network (RAN) engineers.

Your capabilities include:
- ANALYTICS: Detect performance anomalies, find degraded clusters, correlate customer experience metrics, detect congestion, generate heatmaps
- RECOMMENDATIONS: Root cause analysis, simulate parameter impacts, generate optimization recommendations  
- AUTOMATION: Create trouble tickets, generate configuration scripts
- FORECASTING: Forecast traffic for events, predict equipment faults, recommend preventive maintenance

You have access to 13 tools:
- 8 tools through AgentCore Gateway (MCP protocol)
- 5 tools via direct Lambda invocation

Help analyze network performance, identify issues, provide recommendations, and enable proactive network management.
Always provide structured, actionable insights backed by data.""",
        tools=[
            # Analytics
            detect_performance_anomalies,
            find_degraded_clusters,
            correlate_cem_with_kpi,
            detect_slice_congestion,
            get_heatmap_data,
            # Recommendations
            perform_root_cause_analysis,
            simulate_parameter_impact,
            generate_optimization_recommendations,
            # Automation
            create_trouble_ticket,
            generate_configuration_script,
            # Forecasting
            forecast_traffic_for_event,
            predict_equipment_faults,
            recommend_preventive_maintenance
        ]
    )
    logger.info("✓ Strands Agent initialized successfully!")
except Exception as e:
    logger.error(f"✗ Failed to initialize Strands Agent: {e}")
    import traceback
    traceback.print_exc()
    strands_agent = None

# ============================================================================
# Models & Endpoints
# ============================================================================

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

@app.get("/ping")
async def ping():
    """Health check endpoint."""
    logger.info("Ping received")
    return {"status": "healthy"}

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """Main invocation endpoint for the Bedrock AgentCore Runtime."""
    logger.info("=" * 60)
    logger.info("INVOCATIONS ENDPOINT CALLED")
    logger.info("=" * 60)
    
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            logger.error("No prompt found in input")
            raise HTTPException(status_code=400, detail="No prompt found in input.")
        
        logger.info(f"User message: {user_message}")
        
        if strands_agent is None:
            logger.error("Agent failed to initialize at startup")
            raise HTTPException(status_code=500, detail="Agent failed to initialize.")
        
        logger.info("Calling Strands Agent...")
        result = strands_agent(user_message)
        logger.info("Agent call completed successfully")
        
        response = {
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "strands-agent",
            "gateway_arn": GATEWAY_ARN,
        }
        
        return InvocationResponse(output=response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting RAN Co-pilot Agent on 0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
