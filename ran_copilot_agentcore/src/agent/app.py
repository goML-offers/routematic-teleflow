"""
RAN Co-pilot Agent - FastAPI Implementation for AgentCore Runtime
Simplified and production-ready version matching the working sample from documentation.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json
import logging
import boto3
import os

from strands import Agent, tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="RAN Co-pilot Agent", version="1.0.0")

# Initialize AWS Lambda client for tool invocation
lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'ap-south-1'))

# ============================================================================
# Lambda Invocation Wrapper
# ============================================================================

def invoke_lambda_tool(function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invokes a Lambda function through AWS Lambda.
    This bridges the Strands tools with the actual Lambda functions deployed in AWS.
    
    Args:
        function_name: Name of the Lambda function to invoke
        payload: Input payload for the Lambda function
    
    Returns:
        Response from the Lambda function
    """
    try:
        logger.info(f"Invoking Lambda function: {function_name}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(payload)
        )
        
        # Parse the response
        response_payload = json.loads(response['Payload'].read())
        logger.info(f"Lambda response: {json.dumps(response_payload, default=str)[:200]}")
        
        return response_payload
    except Exception as e:
        logger.error(f"Error invoking Lambda function {function_name}: {str(e)}")
        # Return a mock response to prevent tool failures
        return {"error": str(e), "tool": function_name, "status": "failed"}

# ============================================================================
# ANALYTICS TOOLS (Agent: Analytics)
# ============================================================================

@tool()
def detect_performance_anomalies(kpi_name: str, time_window: str = "24h") -> dict:
    """
    Identifies statistical deviations in time-series KPI data.
    Detects anomalies in signal strength (RSRP), signal quality (SINR), cell ID changes, etc.
    """
    logger.info(f"Tool: detect_performance_anomalies - KPI: {kpi_name}, Window: {time_window}")
    
    # Try to invoke Lambda, fall back to mock if unavailable
    try:
        result = invoke_lambda_tool(
            'detect-performance-anomalies',
            {"kpi_name": kpi_name, "time_window": time_window}
        )
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "anomalies": [
                {"cell_id": "cell_001", "kpi": kpi_name, "deviation": -8.5, "severity": "high"},
                {"cell_id": "cell_002", "kpi": kpi_name, "deviation": -5.2, "severity": "medium"}
            ],
            "tool": "analytics_detect_anomalies",
            "source": "mock"
        }

@tool()
def find_degraded_clusters() -> dict:
    """
    Identifies cell clusters with degraded performance based on RSRP metrics.
    Returns clusters sorted by severity of degradation.
    """
    logger.info("Tool: find_degraded_clusters")
    
    try:
        result = invoke_lambda_tool('find-degraded-cell-clusters', {})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "degraded_clusters": [
                {"cluster_id": "cluster_01", "avg_rsrp": -95, "affected_cells": 3},
                {"cluster_id": "cluster_02", "avg_rsrp": -98, "affected_cells": 5}
            ],
            "tool": "analytics_find_clusters",
            "source": "mock"
        }

@tool()
def correlate_cem_with_kpi(kpi_type: str = "signal_strength") -> dict:
    """
    Correlates Customer Experience Metrics (CEM) scores with key KPIs.
    Analyzes relationship between network metrics and user experience.
    """
    logger.info(f"Tool: correlate_cem_with_kpi - KPI Type: {kpi_type}")
    
    try:
        result = invoke_lambda_tool('correlate-kpi-with-cem', {"kpi_type": kpi_type})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "correlations": [
                {"kpi": kpi_type, "cem_score": 78, "correlation_strength": 0.82},
                {"kpi": "latency", "cem_score": 65, "correlation_strength": 0.91}
            ],
            "tool": "analytics_correlate_cem",
            "source": "mock"
        }

@tool()
def detect_slice_congestion(slice_id: str) -> dict:
    """
    Detects network slice congestion based on downlink BLER and throughput metrics.
    Identifies slices operating above capacity thresholds.
    """
    logger.info(f"Tool: detect_slice_congestion - Slice: {slice_id}")
    
    try:
        result = invoke_lambda_tool('detect-slice-congestion', {"slice_id": slice_id})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "is_congested": False,
            "current_load": 75,
            "threshold": 85,
            "details": f"Slice {slice_id} operating at normal capacity",
            "tool": "analytics_detect_congestion",
            "source": "mock"
        }

@tool()
def get_heatmap_data(kpi_name: str = "signal_strength", format_type: str = "geojson") -> dict:
    """
    Generates geographic heatmap data for visualization of KPI metrics across the network.
    Returns GeoJSON format for web visualization of cell coverage and performance.
    """
    logger.info(f"Tool: get_heatmap_data - KPI: {kpi_name}, Format: {format_type}")
    
    try:
        result = invoke_lambda_tool(
            'get-kpi-heatmap-data',
            {"kpi_name": kpi_name, "format_type": format_type}
        )
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [28.7041, 77.1025]},
                    "properties": {"cell_id": "cell_001", "signal_strength": -85, "color": "#FF5733"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [28.7045, 77.1030]},
                    "properties": {"cell_id": "cell_002", "signal_strength": -90, "color": "#FFC300"}
                }
            ],
            "tool": "analytics_get_heatmap",
            "source": "mock"
        }

# ============================================================================
# RECOMMENDATION TOOLS (Agent: Recommendation & Optimization)
# ============================================================================

@tool()
def perform_root_cause_analysis(issue_type: str) -> dict:
    """
    Performs root cause analysis for detected network issues.
    Analyzes fault management alarms and correlates with KPI degradation patterns.
    """
    logger.info(f"Tool: perform_root_cause_analysis - Issue: {issue_type}")
    
    try:
        result = invoke_lambda_tool('perform-root-cause-analysis', {"issue_type": issue_type})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "root_causes": [
                {"cause": "High interference on cell_001", "probability": 0.85, "severity": "high"},
                {"cause": "Load imbalance between clusters", "probability": 0.60, "severity": "medium"}
            ],
            "recommended_actions": ["Perform interference analysis", "Rebalance cell loads"],
            "tool": "recommendation_perform_rca",
            "source": "mock"
        }

@tool()
def simulate_parameter_impact(parameter_name: str, proposed_value: Any) -> dict:
    """
    Simulates the impact of proposed parameter changes on network performance.
    Returns predicted KPI changes and potential side effects.
    """
    logger.info(f"Tool: simulate_parameter_impact - Parameter: {parameter_name}, Value: {proposed_value}")
    
    try:
        result = invoke_lambda_tool(
            'simulate-parameter-change-impact',
            {"parameter_name": parameter_name, "proposed_value": proposed_value}
        )
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "parameter": parameter_name,
            "proposed_value": proposed_value,
            "predicted_impact": {
                "kpi_changes": {"RSRP": +2.5, "SINR": +1.8, "throughput": +5.2},
                "risk_level": "low",
                "affected_cells": 3
            },
            "tool": "recommendation_simulate_impact",
            "source": "mock"
        }

@tool()
def generate_optimization_recommendations() -> dict:
    """
    Generates structured optimization recommendations based on RCA and simulation results.
    Returns prioritized list of configuration changes and their expected benefits.
    """
    logger.info("Tool: generate_optimization_recommendations")
    
    try:
        result = invoke_lambda_tool('generate-optimization-recommendation', {})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "recommendations": [
                {
                    "priority": 1,
                    "action": "Increase antenna tilt on cell_001",
                    "expected_benefit": "Reduce interference by 15%",
                    "effort": "low",
                    "risk": "minimal"
                },
                {
                    "priority": 2,
                    "action": "Load balance traffic to cluster_02",
                    "expected_benefit": "Improve RSRP by 3dB",
                    "effort": "medium",
                    "risk": "low"
                }
            ],
            "tool": "recommendation_generate_reco",
            "source": "mock"
        }

# ============================================================================
# AUTOMATION TOOLS (Agent: Automation & Execution)
# ============================================================================

@tool()
def create_trouble_ticket(issue_title: str, severity: str, description: str) -> dict:
    """
    Creates a trouble ticket for network issues requiring human intervention.
    Integrates with ticketing system for issue tracking and escalation.
    """
    logger.info(f"Tool: create_trouble_ticket - Title: {issue_title}, Severity: {severity}")
    
    try:
        result = invoke_lambda_tool(
            'create-trouble-ticket',
            {"issue_title": issue_title, "severity": severity, "description": description}
        )
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "ticket_id": "TKT-2025-001234",
            "status": "created",
            "title": issue_title,
            "severity": severity,
            "assigned_to": "RAN_Team",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tool": "automation_create_ticket",
            "source": "mock"
        }

@tool()
def generate_configuration_script(changes: Dict[str, Any]) -> dict:
    """
    Generates configuration scripts for automated parameter updates.
    Produces commands ready for execution on network elements.
    """
    logger.info(f"Tool: generate_configuration_script - Changes: {list(changes.keys())}")
    
    try:
        result = invoke_lambda_tool('generate-configuration-script', {"changes": changes})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "script_id": "SCRIPT-20250101-001",
            "generated_commands": [
                "configure cell_001 antenna_tilt 5",
                "configure cell_002 power_level 20",
                "apply_changes all_cells"
            ],
            "execution_time_estimate": "30 minutes",
            "rollback_available": True,
            "tool": "automation_generate_script",
            "source": "mock"
        }

# ============================================================================
# FORECASTING TOOLS (Agent: Forecasting & Proactive)
# ============================================================================

@tool()
def forecast_traffic_for_event(event_name: str, event_date: str, location: str) -> dict:
    """
    Forecasts network traffic patterns for upcoming events.
    Predicts peak loads and recommends preemptive optimization measures.
    """
    logger.info(f"Tool: forecast_traffic_for_event - Event: {event_name}, Date: {event_date}")
    
    try:
        result = invoke_lambda_tool(
            'forecast-traffic-for-event',
            {"event_name": event_name, "event_date": event_date, "location": location}
        )
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "event": event_name,
            "date": event_date,
            "location": location,
            "predicted_peak_load": 92,
            "peak_time": "18:00-20:00",
            "recommended_actions": [
                "Increase cell capacity by 20%",
                "Pre-activate standby cells",
                "Load balance to underutilized clusters"
            ],
            "tool": "forecasting_traffic_for_event",
            "source": "mock"
        }

@tool()
def predict_equipment_faults(cell_id: Optional[str] = None) -> dict:
    """
    Predicts potential equipment faults based on historical patterns and current metrics.
    Enables proactive maintenance before failures occur.
    """
    logger.info(f"Tool: predict_equipment_faults - Cell: {cell_id}")
    
    try:
        result = invoke_lambda_tool('predict-equipment-faults', {"cell_id": cell_id})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "predictions": [
                {"equipment": "RRU_cell_001", "fault_type": "thermal_issue", "probability": 0.78, "days_to_failure": 7},
                {"equipment": "PSU_cell_002", "fault_type": "power_degradation", "probability": 0.45, "days_to_failure": 14}
            ],
            "critical_alerts": 1,
            "tool": "forecasting_predict_faults",
            "source": "mock"
        }

@tool()
def recommend_preventive_maintenance() -> dict:
    """
    Recommends preventive maintenance actions based on equipment age, usage patterns, and failure predictions.
    Schedules maintenance to minimize network disruption.
    """
    logger.info("Tool: recommend_preventive_maintenance")
    
    try:
        result = invoke_lambda_tool('recommend-preventive-maintenance', {})
        return result
    except Exception as e:
        logger.warning(f"Lambda invocation failed, using mock data: {e}")
        return {
            "maintenance_plan": [
                {
                    "equipment": "RRU_cell_001",
                    "action": "Thermal system inspection",
                    "scheduled_date": "2025-01-28",
                    "estimated_downtime": "1 hour",
                    "priority": "high"
                },
                {
                    "equipment": "PSU_cell_002",
                    "action": "Power supply replacement",
                    "scheduled_date": "2025-02-15",
                    "estimated_downtime": "30 minutes",
                    "priority": "medium"
                }
            ],
            "tool": "forecasting_recommend_maintenance",
            "source": "mock"
        }

# Initialize Strands Agent with all 13 tools
logger.info("Initializing Strands Agent with 13 integrated tools...")
try:
    strands_agent = Agent(
        system_prompt="""You are an intelligent RAN Co-pilot assistant for Radio Access Network (RAN) engineers.
        
Your capabilities include:
- ANALYTICS: Detect performance anomalies, find degraded clusters, correlate customer experience metrics, detect congestion, generate heatmaps
- RECOMMENDATIONS: Root cause analysis, simulate parameter impacts, generate optimization recommendations  
- AUTOMATION: Create trouble tickets, generate configuration scripts
- FORECASTING: Forecast traffic for events, predict equipment faults, recommend preventive maintenance

You help analyze network performance, identify issues, provide recommendations, and enable proactive network management.
Always provide structured, actionable insights backed by data. When users ask about network issues, use the appropriate tools to investigate and provide solutions.""",
        tools=[
            # Analytics Tools (5)
            detect_performance_anomalies,
            find_degraded_clusters,
            correlate_cem_with_kpi,
            detect_slice_congestion,
            get_heatmap_data,
            # Recommendation Tools (3)
            perform_root_cause_analysis,
            simulate_parameter_impact,
            generate_optimization_recommendations,
            # Automation Tools (2)
            create_trouble_ticket,
            generate_configuration_script,
            # Forecasting Tools (3)
            forecast_traffic_for_event,
            predict_equipment_faults,
            recommend_preventive_maintenance
        ]
    )
    logger.info("✓ Strands Agent initialized successfully with 13 tools!")
except Exception as e:
    logger.error(f"✗ Failed to initialize Strands Agent: {e}")
    import traceback
    traceback.print_exc()
    strands_agent = None

# Define request/response models
class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]

# Endpoints
@app.get("/ping")
async def ping():
    """Health check endpoint."""
    logger.info("Ping received")
    return {"status": "healthy"}

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """
    Main invocation endpoint for the Bedrock AgentCore Runtime.
    Receives user input and returns agent response.
    """
    logger.info("=" * 60)
    logger.info("INVOCATIONS ENDPOINT CALLED")
    logger.info("=" * 60)
    
    try:
        # Extract user message from input
        user_message = request.input.get("prompt", "")
        if not user_message:
            logger.error("No prompt found in input")
            raise HTTPException(
                status_code=400,
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )
        
        logger.info(f"User message: {user_message}")
        
        # Check if agent initialized successfully
        if strands_agent is None:
            logger.error("Agent failed to initialize at startup")
            raise HTTPException(
                status_code=500,
                detail="Agent failed to initialize. Check logs for details."
            )
        
        # Call the Strands agent
        logger.info("Calling Strands Agent...")
        result = strands_agent(user_message)
        logger.info("Agent call completed successfully")
        
        # Build response (matching working sample format)
        response = {
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "strands-agent",
        }
        
        logger.info(f"Response built: {json.dumps(response, indent=2, default=str)[:200]}...")
        
        return InvocationResponse(output=response)
    
    except HTTPException as he:
        logger.error(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent processing: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting RAN Co-pilot Agent on 0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
