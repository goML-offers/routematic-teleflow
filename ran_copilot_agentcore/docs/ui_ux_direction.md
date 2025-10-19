# RAN Co-pilot - Deployment & Integration Guide

## Overview

The RAN Co-pilot is a Strands-based AI agent deployed on AWS Bedrock AgentCore Runtime. It provides intelligent network analysis and optimization recommendations through 13 integrated tools.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface                              │
│              (Web Dashboard / Mobile App / CLI)                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          RAN Co-pilot Client (client.py)                         │
│   - Sends prompts via boto3 bedrock-agentcore client             │
│   - Manages session state                                        │
│   - Parses agent responses                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│        AWS Bedrock AgentCore Runtime (Port 8080)                 │
│   - Strands Agent deployed as FastAPI web service               │
│   - /ping endpoint for health checks                             │
│   - /invocations endpoint for agent execution                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────┬────────────┬────────────┬────────────┐
         ↓            ↓            ↓            ↓            ↓
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Analytics│ │Recommend│ │Automate │ │Forecast │ │ Shared  │
    │ Tools   │ │ Tools   │ │ Tools   │ │ Tools   │ │ Library │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
         ↓            ↓            ↓            ↓
    ┌──────────────────────────────────────────────────────┐
    │           AWS Lambda Functions (13 tools)            │
    │  - Actual computation & data processing              │
    │  - Integrate with Amazon Athena for queries          │
    │  - Return structured JSON responses                  │
    └──────────────────────────────────────────────────────┘
         ↓            ↓            ↓            ↓
    ┌──────────────────────────────────────────────────────┐
    │    AWS Data Platform                                 │
    │  - Amazon S3 (Data Lake)                             │
    │  - Amazon Athena (Query Engine)                      │
    │  - AWS Glue (Data Catalog - optional)                │
    └──────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Build the Agent Docker Image

```bash
cd ran_copilot_agentcore

docker buildx build --platform linux/arm64 \
  --provenance=false \
  -t 767828738296.dkr.ecr.ap-south-1.amazonaws.com/ran-copilot-agent:latest \
  --push \
  -f src/agent/Dockerfile .
```

### 2. Deploy to AgentCore Runtime

Use the AWS Console or CLI:

```bash
aws bedrock-agentcore-control create-agent-runtime \
  --agent-runtime-name ran-copilot-agent \
  --agent-runtime-artifact containerConfiguration.containerUri=767828738296.dkr.ecr.ap-south-1.amazonaws.com/ran-copilot-agent:latest \
  --network-configuration networkMode=PUBLIC \
  --role-arn arn:aws:iam::767828738296:role/AgentRuntimeRole \
  --region ap-south-1
```

### 3. Save the Agent Runtime ARN

After deployment, you'll receive an ARN like:
```
arn:aws:bedrock-agentcore:ap-south-1:767828738296:runtime/ran-copilot-agent-xxxxx
```

Add this to your `.env` file:
```
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:ap-south-1:767828738296:runtime/ran-copilot-agent-xxxxx
AWS_REGION=ap-south-1
```

## Testing the Agent

### Option 1: Test Suite

Run all predefined test scenarios:

```bash
python client.py
```

This will test:
- Analytics tools (anomaly detection, cluster analysis, etc.)
- Recommendation tools (RCA, simulation, optimization)
- Automation tools (ticket creation, script generation)
- Forecasting tools (traffic prediction, fault prediction)

### Option 2: Interactive Mode

Launch an interactive session:

```bash
python client.py --interactive
```

Example queries:
```
RAN Co-pilot> Are there any performance anomalies in RSRP?
RAN Co-pilot> Find cell clusters with degraded performance
RAN Co-pilot> Generate optimization recommendations
RAN Co-pilot> exit
```

## The 13 Integrated Tools

### Analytics (5 tools)
1. **detect_performance_anomalies** - Find KPI deviations
2. **find_degraded_clusters** - Identify underperforming cell groups
3. **correlate_cem_with_kpi** - Link user experience to metrics
4. **detect_slice_congestion** - Monitor network slice capacity
5. **get_heatmap_data** - Generate geographic visualizations

### Recommendations (3 tools)
6. **perform_root_cause_analysis** - Analyze fault root causes
7. **simulate_parameter_impact** - Test configuration changes
8. **generate_optimization_recommendations** - Get actionable optimization steps

### Automation (2 tools)
9. **create_trouble_ticket** - Log issues in ticketing system
10. **generate_configuration_script** - Create executable commands

### Forecasting (3 tools)
11. **forecast_traffic_for_event** - Predict load for upcoming events
12. **predict_equipment_faults** - Identify potential failures
13. **recommend_preventive_maintenance** - Schedule maintenance

## Lambda Integration

Each tool can invoke a corresponding Lambda function for real data processing:

```python
# In agent code:
result = invoke_lambda_tool(
    'analytics_detect_anomalies',  # Lambda function name
    {"kpi_name": "RSRP", "time_window": "24h"}  # Input payload
)
```

If Lambda invocation fails, the agent gracefully falls back to mock data, ensuring availability.

## UI/UX Direction

### Key Principles

1. **Conversational First**: Users interact through natural language queries
2. **Contextual Clarity**: Results show which tool was used and data source
3. **Visual Intelligence**: Complex data presented as heatmaps, charts, and tables
4. **Actionable Insights**: Every recommendation includes effort, risk, and expected benefits
5. **Session Persistence**: User context maintained across multiple queries

### Recommended Features

#### Heatmap Visualization
- **Geographic Heatmaps**: Show signal strength, SINR, or throughput across coverage area
- **Color Coding**: 
  - 🟢 Green: Normal performance (>-85 dBm RSRP)
  - 🟡 Yellow: Degraded performance (-85 to -95 dBm)
  - 🔴 Red: Critical performance (<-95 dBm)
- **Interactive**: Click cells to see detailed metrics

#### Recommendation Cards
```
┌─────────────────────────────────┐
│ Priority: 1 (High)              │
├─────────────────────────────────┤
│ Action: Increase antenna tilt   │
│ Expected Benefit: +3dB RSRP     │
│ Effort: Low | Risk: Minimal     │
│ [Approve] [Details] [Simulate]  │
└─────────────────────────────────┘
```

#### Anomaly Alerts
```
⚠️ Alert: High RSRP deviation detected
   Cell: cell_001
   Deviation: -8.5 dB from baseline
   Severity: High
   [Investigate] [Create Ticket]
```

#### Session History
- Track multi-turn conversations
- Reference previous analysis results
- Build complex troubleshooting workflows

## Monitoring & Observability

### CloudWatch Logs

All agent invocations are logged to CloudWatch:

```bash
aws logs tail /aws/bedrock/agentcore/ran-copilot-agent --follow
```

Key log entries:
- Tool invocation timestamps
- Lambda function calls
- Response times
- Error messages

### Metrics

Monitor agent performance:
- Invocation count
- Average response time
- Tool usage distribution
- Lambda timeout rate
- Data accuracy

### Custom Alarms

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ran-copilot-high-latency \
  --metric-name AgentLatency \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Issue: Agent returns mock data instead of real results

**Cause**: Lambda functions are not accessible or not deployed

**Solution**:
1. Verify Lambda functions are deployed
2. Check IAM permissions for AgentCore Runtime role
3. Verify Lambda function names match exactly
4. Check Lambda execution logs in CloudWatch

### Issue: Slow response times

**Cause**: Lambda functions taking long to execute

**Solution**:
1. Increase Lambda timeout (currently 60 seconds)
2. Optimize Athena queries
3. Check data volume in S3
4. Consider data caching layer

### Issue: Tool parameters not being passed correctly

**Cause**: Parameter serialization mismatch

**Solution**:
1. Check Strands tool parameter definitions
2. Verify JSON serialization in invoke_lambda_tool()
3. Test Lambda directly with same payload

## Next Steps

1. ✅ Deploy agent to AgentCore Runtime
2. ✅ Build client application
3. ⏳ Implement real Lambda functions (currently using mock responses)
4. ⏳ Connect to actual Athena queries
5. ⏳ Build web UI dashboard
6. ⏳ Add user authentication
7. ⏳ Set up monitoring and alerts
