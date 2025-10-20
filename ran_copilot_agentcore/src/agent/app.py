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
import random # Added for mock forecast

# Add parent directory to path for imports
sys.path.insert(0, '/app')

from strands import Agent, tool # Re-added 'tool' to the import
from strands.models import BedrockModel # Import BedrockModel
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

SYSTEM_PROMPT = """
You are a RAN Co-pilot, an expert AI assistant for telecommunications engineers. Your persona is helpful, proactive, and concise. Your goal is to provide clear, actionable insights, not just raw data.

**Your Core Directives:**

1.  **Synthesize, Don't Announce:** When a user asks a question, DO NOT list the tools you are going to use. Silently select the appropriate tool, execute it, and then synthesize the results into a friendly, natural language answer. The user should feel like they are talking to an expert, not a command-line interface.

2.  **Interpret the Results:** Never just state what a tool returned.
    *   If a tool returns data (e.g., a list of degraded cells), summarize the key findings. For example: "I've found 3 cells with degraded performance. The most critical one is cell_045, with an RRC success rate of only 91.2%."
    *   If a tool returns no data, interpret what that means. For example, if `predict_equipment_faults` returns nothing, don't say "the tool returned nothing." Say: "Good news, I've run a full diagnostic and all equipment appears to be healthy. No immediate preventive maintenance is required."

3.  **Be Proactive, Not Passive:** Don't just present a menu of options. Based on the user's query and the data you find, suggest a logical next step. For example, after finding degraded cells, you might ask, "Would you like me to perform a root cause analysis on the most critical cell, cell_045?"

**Example Interaction:**

*   **User:** "Are there any degraded cells?"
*   **Your (Bad) Response:** "Certainly! I will use the `find_degraded_clusters` tool..."
*   **Your (Good) Response:** "Yes, I've found 3 cells with degraded performance. The most critical is cell_045, with an RRC success rate of only 91.2%. Would you like me to investigate the root cause for that cell?"
"""

# AWS clients
bedrock_client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
athena_client = boto3.client('athena', region_name=os.getenv('AWS_REGION', 'ap-south-1'))
s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-south-1'))

# Athena configuration
ATHENA_DATABASE = 'ran_copilot'
ATHENA_OUTPUT_LOCATION = 's3://ran-copilot-data-lake/athena-results/'

def run_athena_query(query: str) -> List[Dict[str, Any]]:
    """Execute Athena query and return results"""
    try:
        logger.info(f"Running Athena query: {query}")
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': ATHENA_DATABASE},
            ResultConfiguration={'OutputLocation': ATHENA_OUTPUT_LOCATION}
        )
        query_id = response['QueryExecutionId']
        
        # Wait for query to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            result = athena_client.get_query_execution(QueryExecutionId=query_id)
            if result['QueryExecution']['Status']['State'] in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            if attempt == max_attempts - 1:
                raise Exception("Athena query timeout")
            import time
            time.sleep(1)
        
        if result['QueryExecution']['Status']['State'] != 'SUCCEEDED':
            raise Exception(f"Athena query failed: {result['QueryExecution']['Status']['StateChangeReason']}")
        
        # Get results
        results = athena_client.get_query_results(QueryExecutionId=query_id)
        
        # Parse results
        data = []
        for row in results['ResultSet']['Rows'][1:]:  # Skip header
            values = [cell.get('VarCharValue', '') for cell in row['Data']]
            data.append(values)
        
        logger.info(f"Query returned {len(data)} rows")
        return data
    except Exception as e:
        logger.error(f"Athena query error: {e}")
        # In the context of a tool, we return a dict, not an HTTPException
        return {"status": "failed", "error": f"Database query failed: {str(e)}"}

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
    """
    Finds unusual spikes or dips (anomalies) in a specific network KPI over time. 
    Use this to investigate unexpected network behavior for metrics like throughput, success rates, or network load.
    For example: "Are there any anomalies in throughput in the last 12 hours?", "Check for unusual RRC success rate activity."
    """
    logger.info(f"Tool: detect_performance_anomalies - KPI: {kpi_name}, Window: {time_window}")
    
    # Convert time_window (e.g., "24h") to an integer number of hours
    try:
        hours = int(time_window.replace('h', ''))
    except ValueError:
        return {"status": "failed", "error": "Invalid time_window format. Use '24h', '12h', etc."}

    query = f"""
    WITH kpi_stats AS (
        SELECT
            AVG({kpi_name}) as avg_kpi,
            STDDEV({kpi_name}) as stddev_kpi
        FROM analytics_ue_metrics
    )
    SELECT
        t.cell_id,
        DATE_FORMAT(t.time, '%Y-%m-%d %H:%i:%s') as timestamp,
        t.{kpi_name} as anomalous_value,
        s.avg_kpi,
        s.stddev_kpi
    FROM 
        analytics_ue_metrics t, kpi_stats s
    WHERE 
        ABS(t.{kpi_name} - s.avg_kpi) > (2 * s.stddev_kpi) -- Find values > 2 std deviations from the mean
    ORDER BY
        t.time DESC
    LIMIT 20
    """
    try:
        results = run_athena_query(query)
        anomalies = [
            {
                "cell_id": row[0],
                "timestamp": row[1],
                "anomalous_value": float(row[2]) if row[2] else 0,
                "mean_value": float(row[3]) if row[3] else 0,
                "std_dev": float(row[4]) if row[4] else 0
            }
            for row in results
        ]
        return {
            "status": "success",
            "anomalies_found": len(anomalies),
            "data": anomalies
        }
    except Exception as e:
        logger.error(f"Error in detect_performance_anomalies: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def find_degraded_clusters() -> dict:
    """
    Retrieves the operational status of all network cells, identifying which are Optimal, Degraded, or Critical.
    Use this tool to answer questions about the current status of cells, find degraded cells, or get a list of cell performance.
    For example: "What is the status of the cells?", "Are there any degraded cells?", "Show me the cell performance list."
    """
    logger.info("Tool: find_degraded_clusters")
    
    query = """
    SELECT
        cell_id,
        AVG(rrc_success_rate) as avg_rrc,
        AVG(handover_success_rate) as avg_ho,
        AVG(network_load) as avg_load,
        CASE
            WHEN AVG(rrc_success_rate) > 94.5 THEN 'Optimal'
            WHEN AVG(rrc_success_rate) > 93.5 THEN 'Degraded'
            ELSE 'Critical'
        END as status
    FROM
        analytics_ue_metrics
    GROUP BY
        cell_id
    HAVING
        AVG(rrc_success_rate) <= 94.5 -- Return all non-Optimal cells
    ORDER BY
        avg_rrc ASC
    LIMIT 50
    """
    try:
        results = run_athena_query(query)
        degraded_cells = [
            {
                "cell_id": row[0],
                "avg_rrc_success_rate": float(row[1]) if row[1] else 0,
                "avg_handover_success_rate": float(row[2]) if row[2] else 0,
                "avg_network_load": float(row[3]) if row[3] else 0,
                "status": row[4]
            }
            for row in results
        ]
        return {
            "status": "success",
            "degraded_cells_found": len(degraded_cells),
            "data": degraded_cells
        }
    except Exception as e:
        logger.error(f"Error in find_degraded_clusters: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def correlate_cem_with_kpi(kpi_type: str = "signal_strength") -> dict:
    """Correlates Customer Experience Metrics (CEM) scores with key KPIs."""
    logger.info(f"Tool: correlate_cem_with_kpi - KPI Type: {kpi_type}")
    
    # This is a simplified correlation. A real-world scenario would use more advanced statistical models.
    # Here, we're finding the correlation between user-reported 'satisfaction_score' and network KPIs.
    query = f"""
    SELECT
        corr(satisfaction_score, rrc_success_rate) as corr_rrc,
        corr(satisfaction_score, handover_success_rate) as corr_handover,
        corr(satisfaction_score, throughput_mbps) as corr_throughput,
        corr(satisfaction_score, network_load) as corr_load
    FROM
        analytics_cem_metrics
    """
    try:
        results = run_athena_query(query)
        if not results:
            return {"status": "success", "data": {}}

        row = results[0]
        correlations = {
            "rrc_success_rate": float(row[0]) if row[0] else 0,
            "handover_success_rate": float(row[1]) if row[1] else 0,
            "throughput_mbps": float(row[2]) if row[2] else 0,
            "network_load": float(row[3]) if row[3] else 0,
        }
        return {
            "status": "success",
            "data": correlations
        }
    except Exception as e:
        logger.error(f"Error in correlate_cem_with_kpi: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def detect_slice_congestion(slice_id: str) -> dict:
    """Detects network slice congestion based on resource utilization metrics."""
    logger.info(f"Tool: detect_slice_congestion - Slice: {slice_id}")

    query = f"""
    SELECT
        slice_id,
        AVG(prb_utilization) as avg_prb_utilization,
        AVG(throughput_mbps) as avg_throughput
    FROM
        analytics_slice_metrics
    WHERE
        slice_id = '{slice_id}'
    GROUP BY
        slice_id
    """
    try:
        results = run_athena_query(query)
        if not results:
            return {
                "status": "success",
                "is_congested": False,
                "details": "No data available for this slice."
            }

        row = results[0]
        prb_utilization = float(row[1]) if row[1] else 0
        
        is_congested = prb_utilization > 85  # Congestion threshold: 85% PRB utilization

        return {
            "status": "success",
            "is_congested": is_congested,
            "slice_id": row[0],
            "avg_prb_utilization": prb_utilization,
            "avg_throughput_mbps": float(row[2]) if row[2] else 0
        }
    except Exception as e:
        logger.error(f"Error in detect_slice_congestion: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def get_heatmap_data(kpi_name: str = "signal_strength", format_type: str = "geojson") -> dict:
    """
    Creates a geographical heatmap for a specific KPI to visualize its performance across different locations. 
    Use this to see the geographic distribution of network quality.
    For example: "Show me a heatmap of throughput", "Generate a map of signal strength across the network."
    """
    logger.info(f"Tool: get_heatmap_data - KPI: {kpi_name}, Format: {format_type}")
    
    query = f"""
    SELECT
        latitude,
        longitude,
        AVG({kpi_name}) as avg_kpi_value
    FROM
        analytics_ue_metrics
    WHERE
        latitude IS NOT NULL
        AND longitude IS NOT NULL
    GROUP BY
        latitude, longitude
    LIMIT 500 -- Limit to avoid excessively large geojson objects
    """
    try:
        results = run_athena_query(query)
        
        # Format as GeoJSON FeatureCollection
        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row[1]), float(row[0])]  # [longitude, latitude]
                },
                "properties": {
                    "kpi_value": float(row[2]) if row[2] else 0
                }
            }
            for row in results if row[0] and row[1]
        ]
        
        geojson_data = {
            "type": "FeatureCollection",
            "features": features
        }
        
        return {
            "status": "success",
            "format": "geojson",
            "data": geojson_data
        }
    except Exception as e:
        logger.error(f"Error in get_heatmap_data: {e}")
        return {"status": "failed", "error": str(e)}

# ============================================================================
# RECOMMENDATION TOOLS (3 total: all Gateway)
# ============================================================================

@tool()
def perform_root_cause_analysis(issue_type: str, cell_id: str) -> dict:
    """
    Investigates the root cause of a specific issue (like 'low throughput' or 'high call drop rate') for a given cell ID.
    It checks for recent critical alarms and configuration changes to diagnose the problem.
    For example: "What is the root cause of low throughput on cell_021?", "Analyze cell_045 for call drop issues."
    """
    logger.info(f"Tool: perform_root_cause_analysis - Issue: {issue_type}, Cell: {cell_id}")

    # 1. Check for recent critical alarms on the cell
    alarms_query = f"""
    SELECT
        alarm_name,
        alarm_severity,
        DATE_FORMAT(time, '%Y-%m-%d %H:%i:%s') as alarm_time
    FROM
        analytics_alarms
    WHERE
        cell_id = '{cell_id}'
        AND alarm_severity = 'CRITICAL'
    ORDER BY
        time DESC
    LIMIT 5
    """

    # 2. Check for recent configuration changes on the cell
    changes_query = f"""
    SELECT
        parameter_name,
        old_value,
        new_value,
        DATE_FORMAT(time, '%Y-%m-%d %H:%i:%s') as change_time
    FROM
        analytics_config_changes
    WHERE
        cell_id = '{cell_id}'
    ORDER BY
        time DESC
    LIMIT 5
    """
    try:
        critical_alarms = run_athena_query(alarms_query)
        config_changes = run_athena_query(changes_query)

        # Synthesize findings
        findings = []
        if critical_alarms:
            findings.append({
                "finding_type": "Recent Critical Alarms",
                "details": [
                    {"name": row[0], "severity": row[1], "time": row[2]} for row in critical_alarms
                ]
            })
        
        if config_changes:
            findings.append({
                "finding_type": "Recent Configuration Changes",
                "details": [
                    {"parameter": row[0], "from": row[1], "to": row[2], "time": row[3]} for row in config_changes
                ]
            })
        
        if not findings:
            likely_cause = "No immediate cause found in recent alarms or config changes. Further investigation of KPIs is needed."
        else:
            likely_cause = f"Potential causes identified: {[f['finding_type'] for f in findings]}"

        return {
            "status": "success",
            "cell_id": cell_id,
            "issue_type": issue_type,
            "likely_cause": likely_cause,
            "evidence": findings
        }

    except Exception as e:
        logger.error(f"Error in perform_root_cause_analysis: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def simulate_parameter_impact(parameter_name: str, proposed_value: Any, cell_id: str) -> dict:
    """
    Predicts the likely impact on key performance indicators (KPIs) if a specific network parameter is changed on a cell. 
    It uses historical data to forecast the outcome. Use this to understand the potential consequences of a configuration change before applying it.
    For example: "Simulate the impact of changing handoverOffset to -2 on cell_010", "What will happen if I set txPower to 15?"
    """
    logger.info(f"Tool: simulate_parameter_impact - Parameter: {parameter_name}, Value: {proposed_value}, Cell: {cell_id}")

    # This is a simplified, heuristic-based simulation. A real version would use a dedicated ML model.
    # We find past instances where this parameter was changed to the proposed value and see what happened to key KPIs.
    query = f"""
    WITH change_times AS (
        SELECT
            time as change_time
        FROM
            analytics_config_changes
        WHERE
            parameter_name = '{parameter_name}'
            AND new_value = '{proposed_value}'
        LIMIT 5
    )
    SELECT
        AVG(t2.rrc_success_rate - t1.rrc_success_rate) as rrc_impact,
        AVG(t2.handover_success_rate - t1.handover_success_rate) as ho_impact,
        AVG(t2.throughput_mbps - t1.throughput_mbps) as throughput_impact
    FROM
        analytics_ue_metrics t1
    JOIN
        analytics_ue_metrics t2 ON t1.cell_id = t2.cell_id
    JOIN
        change_times ct ON t1.time BETWEEN (ct.change_time - interval '1' hour) AND ct.change_time
                         AND t2.time BETWEEN ct.change_time AND (ct.change_time + interval '1' hour)
    """
    try:
        results = run_athena_query(query)
        if not results or not results[0][0]:
            return {
                "status": "success",
                "simulation_result": "No historical data available for this specific parameter change. Impact is unknown."
            }

        row = results[0]
        impact = {
            "rrc_success_rate_change": f"{float(row[0]):+.2f}%" if row[0] else "0.00%",
            "handover_success_rate_change": f"{float(row[1]):+.2f}%" if row[1] else "0.00%",
            "throughput_mbps_change": f"{float(row[2]):+.2f} Mbps" if row[2] else "0.00 Mbps",
        }
        return {
            "status": "success",
            "simulation_result": "Based on historical data, the predicted impact is as follows:",
            "predicted_impact": impact
        }
    except Exception as e:
        logger.error(f"Error in simulate_parameter_impact: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def generate_optimization_recommendations(rca_output: dict, simulation_output: dict) -> dict:
    """Generates structured optimization recommendations based on RCA and simulation."""
    logger.info("Tool: generate_optimization_recommendations")

    # This tool synthesizes inputs from other tools into a final recommendation.
    # It's more about logic and formatting than data querying.
    try:
        # Extract key info from RCA
        cell_id = rca_output.get("cell_id", "N/A")
        issue_type = rca_output.get("issue_type", "N/A")
        likely_cause = rca_output.get("likely_cause", "Undetermined")

        # Extract key info from Simulation
        predicted_impact = simulation_output.get("predicted_impact", {})
        impact_summary = ", ".join([f"{k}: {v}" for k, v in predicted_impact.items()])

        # Simple rule-based logic to generate a title and description
        if "Recent Configuration Changes" in likely_cause:
            title = f"Revert recent config change on Cell {cell_id}"
            description = f"The root cause for {issue_type} on cell {cell_id} is likely a recent parameter change. Reverting the change is predicted to have the following impact: {impact_summary}."
        elif "Recent Critical Alarms" in likely_cause:
            title = f"Investigate critical alarms on Cell {cell_id}"
            description = f"The root cause for {issue_type} is linked to critical alarms. A trouble ticket should be created for a field technician to investigate the hardware. The issue does not appear to be related to configuration."
        else:
            title = f"Manual investigation required for {issue_type} on Cell {cell_id}"
            description = "The root cause could not be automatically determined. Further manual analysis is recommended."

        recommendation = {
            "recommendation_id": f"REC-{cell_id}-{int(datetime.now().timestamp())}",
            "title": title,
            "justification": f"RCA suggests the likely cause is: {likely_cause}.",
            "impact_analysis": f"Simulation predicts the following impact: {impact_summary or 'N/A'}",
            "steps": [
                "1. Review the detailed evidence provided in the RCA.",
                "2. If a config change is implicated, prepare a rollback script.",
                "3. If alarms are implicated, dispatch a technician.",
                "4. Monitor KPIs closely after implementing the change."
            ]
        }
        
        return {
            "status": "success",
            "recommendation": recommendation
        }
    except Exception as e:
        logger.error(f"Error in generate_optimization_recommendations: {e}")
        return {"status": "failed", "error": str(e)}

# ============================================================================
# AUTOMATION TOOLS (2 total: both Lambda-only)
# ============================================================================

@tool()
def create_trouble_ticket(issue_title: str, severity: str, description: str) -> dict:
    """
    Creates a formal trouble ticket in the ticketing system for a network issue that requires manual intervention by a field engineer. 
    Use this when a problem has been identified that cannot be solved automatically.
    For example: "Create a critical ticket for the power failure on cell_033", "Open a ticket about the high temperature alarm."
    """
    logger.info(f"Tool: create_trouble_ticket - Title: {issue_title}, Severity: {severity}")
    
    # In a real implementation, this would make an API call to a ticketing system like Jira or ServiceNow.
    # Example using httpx:
    # try:
    #     client = httpx.Client()
    #     response = client.post(
    #         "https://api.servicenow.com/v1/incident",
    #         json={"short_description": issue_title, "urgency": severity, "comments": description},
    #         headers={"Authorization": "Bearer YOUR_API_TOKEN"}
    #     )
    #     response.raise_for_status()
    #     ticket_data = response.json()
    #     return {"status": "success", "ticket_id": ticket_data['result']['number']}
    # except Exception as e:
    #     return {"status": "failed", "error": str(e)}
    
    # Mock implementation
    ticket_id = f"INC-{int(datetime.now().timestamp())}"
    logger.info(f"Mock ticket created: {ticket_id}")
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "message": f"Successfully created mock trouble ticket {ticket_id}."
    }

@tool()
def generate_configuration_script(changes: Dict[str, Any], vendor: str = "Ericsson") -> dict:
    """
    Generates a vendor-specific configuration script (e.g., MML for Ericsson) to apply recommended parameter changes to a network cell. 
    Use this to automate the final step of a network optimization task.
    For example: "Generate a script to set txPower to 15 for cell_010."
    """
    logger.info(f"Tool: generate_configuration_script - Changes: {list(changes.keys())}, Vendor: {vendor}")
    
    # This is a mock script generator. A real implementation would use templates
    # specific to the vendor and equipment model.
    try:
        if vendor.lower() == "ericsson":
            script_lines = ["# Ericsson MML Script"]
            for param, value in changes.items():
                script_lines.append(f"SET_PARAMETER: {param}={value};")
            script_body = "\n".join(script_lines)
            script_lang = "MML"
        elif vendor.lower() == "nokia":
            script_lines = ["<!-- Nokia NetConf Script -->", "<config>"]
            for param, value in changes.items():
                script_lines.append(f"  <{param}>{value}</{param}>")
            script_lines.append("</config>")
            script_body = "\n".join(script_lines)
            script_lang = "XML_NetConf"
        else:
            return {"status": "failed", "error": "Unsupported vendor"}

        return {
            "status": "success",
            "vendor": vendor,
            "script_language": script_lang,
            "script_body": script_body
        }
    except Exception as e:
        logger.error(f"Error in generate_configuration_script: {e}")
        return {"status": "failed", "error": str(e)}

# ============================================================================
# FORECASTING TOOLS (3 total: 2 Gateway + 1 Lambda)
# ============================================================================

@tool()
def forecast_traffic_for_event(event_name: str, event_date: str, location: str) -> dict:
    """Forecasts network traffic by analyzing historical data from similar past events."""
    logger.info(f"Tool: forecast_traffic_for_event - Event: {event_name}, Date: {event_date}, Location: {location}")

    # This is a mock implementation as we don't have event data.
    # In a real scenario, this would query a detailed event traffic table.
    logger.warning("forecast_traffic_for_event is using a mock implementation.")
    
    # Find a baseline from overall traffic
    query = """
    SELECT AVG(throughput_mbps) * 1000 AS avg_traffic_gb_daily 
    FROM analytics_ue_metrics
    """
    try:
        baseline_results = run_athena_query(query)
        baseline_gb = float(baseline_results[0][0]) if baseline_results else 500

        # Generate a plausible-looking daily traffic curve
        peak_hour = 19 # 7 PM
        forecast_timeseries = []
        for hour in range(24):
            # Simple parabolic curve peaking at peak_hour
            factor = max(0.1, 1 - ((hour - peak_hour)**2) / 144)
            predicted_traffic = baseline_gb * factor * random.uniform(1.5, 2.5) # Event multiplier
            forecast_timeseries.append({
                "hour_of_day": hour,
                "predicted_traffic_gb": round(predicted_traffic / 24, 2)
            })

        return {
            "status": "success",
            "event_name": event_name,
            "forecast_timeseries": forecast_timeseries
        }
    except Exception as e:
        logger.error(f"Error in forecast_traffic_for_event: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def predict_equipment_faults(cell_id: Optional[str] = None) -> dict:
    """
    Proactively predicts potential equipment faults by analyzing patterns of recent minor alarms on a cell or across the entire network. 
    Use this to identify hardware that is at risk of failing soon.
    For example: "Are there any cells at risk of equipment failure?", "Predict faults for cell_007."
    """
    logger.info(f"Tool: predict_equipment_faults - Cell: {cell_id}")
    
    # Simplified prediction: A high count of minor alarms often precedes a major fault.
    # We'll flag any cell with more than 10 minor alarms in the last 7 days.
    where_clause = f"AND cell_id = '{cell_id}'" if cell_id else ""
    query = f"""
    SELECT
        cell_id,
        COUNT(*) as minor_alarm_count
    FROM
        analytics_alarms
    WHERE
        alarm_severity = 'MINOR'
        {where_clause}
    GROUP BY
        cell_id
    HAVING
        COUNT(*) > 10 -- Threshold for potential fault
    ORDER BY
        minor_alarm_count DESC
    LIMIT 20
    """
    try:
        results = run_athena_query(query)
        potential_faults = [
            {
                "cell_id": row[0],
                "contributing_factor": "High count of minor alarms",
                "minor_alarm_count": int(row[1]) if row[1] else 0,
                "fault_probability": min(0.5 + (int(row[1]) - 10) * 0.05, 0.95) # Heuristic probability
            }
            for row in results
        ]
        
        return {
            "status": "success",
            "potential_faults_found": len(potential_faults),
            "data": potential_faults
        }
    except Exception as e:
        logger.error(f"Error in predict_equipment_faults: {e}")
        return {"status": "failed", "error": str(e)}

@tool()
def recommend_preventive_maintenance() -> dict:
    """
    Analyzes the output of fault predictions and recommends specific preventive maintenance actions for cells that are at high risk of hardware failure. 
    Use this to get a maintenance schedule.
    For example: "What preventive maintenance is recommended?", "Generate a maintenance plan based on fault predictions."
    """
    logger.info("Tool: recommend_preventive_maintenance")

    # This tool uses the output of `predict_equipment_faults` to generate recommendations.
    try:
        fault_predictions = predict_equipment_faults()
        
        if fault_predictions.get("status") != "success" or not fault_predictions.get("data"):
            return {
                "status": "success",
                "recommendations": "No equipment faults predicted at this time. No preventive maintenance is recommended."
            }

        recommendations = []
        for fault in fault_predictions["data"]:
            cell_id = fault["cell_id"]
            probability = fault["fault_probability"]
            if probability > 0.75:
                action = "Immediate inspection required"
            else:
                action = "Schedule routine check within 7 days"
            
            recommendations.append({
                "cell_id": cell_id,
                "predicted_fault_probability": probability,
                "recommended_action": action,
                "justification": fault["contributing_factor"]
            })

        return {
            "status": "success",
            "recommendations_generated": len(recommendations),
            "data": recommendations
        }
    except Exception as e:
        logger.error(f"Error in recommend_preventive_maintenance: {e}")
        return {"status": "failed", "error": str(e)}

# --- Agent Initialization ---

# Collect all functions decorated with @tool into a list
ALL_TOOLS = [
    detect_performance_anomalies,
    find_degraded_clusters,
    correlate_cem_with_kpi,
    detect_slice_congestion,
    get_heatmap_data,
    perform_root_cause_analysis,
    simulate_parameter_impact,
    generate_optimization_recommendations,
    create_trouble_ticket,
    generate_configuration_script,
    predict_equipment_faults,
    recommend_preventive_maintenance,
]

# Initialize Strands Agent
logger.info("Initializing Strands Agent...")
try:
    # Explicitly configure the BedrockModel to disable streaming.
    # This ensures the agent completes its full thought->action->observation loop
    # and returns a single, final answer, which is required by the Bedrock Agent Runtime.
    bedrock_model = BedrockModel(
        model_id="apac.amazon.nova-pro-v1:0",
        stream=False
    )

    # Use the region-specific model ID for Nova Pro to support on-demand throughput.
    agent = Agent(
        model=bedrock_model,
        system_prompt=SYSTEM_PROMPT,
        tools=ALL_TOOLS  # Explicitly provide the list of executable tools
    )
    logger.info("Strands Agent initialized successfully in non-streaming mode with all tools.")
except Exception as e:
    logger.error(f"Failed to initialize Strands Agent: {e}", exc_info=True)
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")
    agent = None

# ============================================================================
# Models & Endpoints
# ============================================================================

class InvocationRequest(BaseModel):
    input: Dict[str, Any]

class InvocationResponse(BaseModel):
    output: Dict[str, Any]


# REST API Endpoints

@app.post("/invocations", response_model=InvocationResponse)
async def invocations(request: InvocationRequest):
    """Main agent invocation endpoint"""
    try:
        logger.info(f"Received invocation request: {request.input}")
        
        user_prompt = request.input.get('prompt', '')
        logger.info(f"User prompt: {user_prompt}")
        
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Invoke agent by calling it directly (Strands Agent is callable)
        try:
            logger.info("Invoking Strands Agent...")
            result = agent(user_prompt)
            logger.info(f"Agent result type: {type(result)}")
            logger.info(f"Agent result: {result}")
            
            # Convert result to string
            response_text = str(result) if result else "No response"
            
            logger.info(f"Response text: {response_text}")
            
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
            raise HTTPException(status_code=500, detail=f"Agent failed to process the request: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invocation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
