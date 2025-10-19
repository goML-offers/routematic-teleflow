# RAN Co-pilot Frontend Integration Summary

## 📊 Current Status

### ✅ Backend (Complete)
- [x] Agent deployed to AWS AgentCore Runtime
- [x] 13 Lambda tools integrated (8 via Gateway, 5 via direct Lambda)
- [x] REST API endpoints created
- [x] CORS enabled for frontend integration
- [x] Mock data endpoints working
- [x] React integration guide provided

### ⏳ Frontend (In Progress - UI Team)
- [ ] React dashboard application
- [ ] Component implementation
- [ ] API integration
- [ ] Real-time data visualization

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (React)                    │
├─────────────────────────────────────────────────────────────┤
│  Dashboard Header │ Map │ Analytics │ Table │ Co-pilot Chat  │
└────────┬──────────────────────────────────────────────────┬──┘
         │                                                  │
         ├─────────────── HTTP/CORS ──────────────────────┤
         │                                                  │
         ▼                                                  ▼
    ┌────────────────────────────────────────────────────────────┐
    │           FastAPI Backend (Port 8080)                      │
    ├────────────────────────────────────────────────────────────┤
    │  GET  /ping                      - Health check            │
    │  POST /invocations               - Agent invocation        │
    │  GET  /api/dashboard/kpis        - Dashboard metrics       │
    │  GET  /api/cells/status          - Cell locations/status   │
    │  GET  /api/analytics/timeseries  - KPI trends (24h)        │
    │  GET  /api/cells/performance     - Cell details table      │
    └────┬──────────────┬──────────────┬───────────┬─────────────┘
         │              │              │           │
         ▼              ▼              ▼           ▼
    ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
    │   Strands   │ │ Gateway  │ │ Lambda   │ │   Athena     │
    │   Agent     │ │ (MCP)    │ │ Tools    │ │   (SQL)      │
    │             │ │ 8 tools  │ │ 5 tools  │ │              │
    └─────────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## 🎨 Frontend Architecture (UI Team)

### 1. **Dashboard Header**
```
┌─────────────────────────────────────────────────────────┐
│  System Status: Operational                             │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ RRC Success Rate │  │  Active Cells    │             │
│  │     98.5%        │  │        25        │             │
│  │     ↑            │  │        ✓         │             │
│  └──────────────────┘  └──────────────────┘             │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ Critical Alarms  │  │ Network Load     │             │
│  │        3         │  │      62.5%       │             │
│  │        ✓         │  │        →         │             │
│  └──────────────────┘  └──────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 2. **Main Canvas (3 Views)**

#### A. Geospatial View (Mapbox GL)
- **Purpose**: Visualize cell locations and network health geographically
- **Data**: Cell coordinates, status (Optimal/Degraded/Critical), load percentage
- **Features**:
  - Cell markers color-coded by status
  - Click for detailed cell information
  - Heatmap overlay for KPI values
  - Zoom, pan, navigation controls

#### B. Analytics View (Recharts)
- **Purpose**: Display time-series trends and network metrics
- **Charts**:
  - KPI Trends: RRC Success Rate & Handover Success Rate (24h)
  - Network Throughput: Throughput over time
  - Alarm Distribution: Count by severity
  - AI Insights: Summary card with predictions
- **Data Format**: Timestamp, RRC rate, Handover rate, Throughput

#### C. Data Table View
- **Purpose**: Sortable cell performance metrics
- **Columns**: Cell ID, RRC Success %, Handover %, Load %, Alarms, Status
- **Data Format**: Cell records with all performance metrics

### 3. **Co-pilot Panel (Right Sidebar)**
- **Purpose**: Conversational AI assistant for RAN operations
- **Components**:
  - Message history (scrollable)
  - User/Assistant message differentiation
  - Recommendation cards with Action buttons
  - Input field with Send button
- **Features**:
  - Natural language queries
  - Structured recommendations (title, description, impact)
  - Approve/Reject decision buttons
  - Timestamp on all messages

---

## 🔌 API Integration Points

### Endpoint 1: Dashboard KPIs
```http
GET /api/dashboard/kpis

Response:
{
  "rrc_success_rate": 98.5,
  "active_cells": 25,
  "critical_alarms": 3,
  "network_load": 62.5,
  "status": "Operational"
}
```

**Used by**: Dashboard Header component
**Refresh Rate**: Every 30 seconds (optional)

---

### Endpoint 2: Cell Status (for Map)
```http
GET /api/cells/status

Response:
[
  {
    "cell_id": "cell_001",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "status": "Optimal",
    "load_percentage": 45,
    "rrc_success_rate": 98.5
  },
  ...
]
```

**Used by**: Geospatial View component
**Refresh Rate**: Every 30 seconds (optional)

---

### Endpoint 3: Time-Series Analytics
```http
GET /api/analytics/timeseries?metric=rrc_success_rate&hours=24

Response:
[
  {
    "timestamp": "2025-10-20T00:00:00Z",
    "rrc_success_rate": 98.5,
    "handover_success_rate": 97.2,
    "throughput_mbps": 125.3
  },
  ...
]
```

**Used by**: Analytics View charts
**Parameters**:
- `metric`: One of `rrc_success_rate`, `handover_rate`, `throughput`
- `hours`: Number of hours of history (default: 24)

---

### Endpoint 4: Cell Performance (Table Data)
```http
GET /api/cells/performance?limit=100

Response:
[
  {
    "cell_id": "cell_001",
    "rrc_success_rate": 98.5,
    "handover_success_rate": 97.2,
    "network_load": 45,
    "active_alarms": 2,
    "status": "Optimal"
  },
  ...
]
```

**Used by**: Data Table View component
**Parameters**:
- `limit`: Maximum records to return (default: 100)

---

### Endpoint 5: Agent Invocation (Chat)
```http
POST /invocations

Request:
{
  "input": {
    "prompt": "Are there any performance anomalies?"
  }
}

Response:
{
  "output": {
    "message": {
      "role": "assistant",
      "content": "I found 5 performance anomalies in the last 24 hours...",
      "timestamp": "2025-10-20T12:30:00Z",
      "recommendation": {
        "title": "Increase Antenna Tilt",
        "description": "Reduce interference on cells...",
        "impact": "Expected 3dB RSRP improvement"
      }
    }
  }
}
```

**Used by**: Co-pilot Panel component
**Features**:
- Natural language input
- Structured recommendation output (optional)
- Timestamp tracking
- Support for action buttons (Approve/Reject)

---

## 🛠️ Implementation Checklist for UI Team

### Phase 1: Setup & Dependencies
- [ ] Create React project (`npx create-react-app ran-copilot-frontend`)
- [ ] Install dependencies:
  ```bash
  npm install axios mapbox-gl recharts
  ```
- [ ] Create `.env.local` with API URL:
  ```env
  REACT_APP_API_URL=http://localhost:8080
  ```

### Phase 2: Core Services
- [ ] Create `src/config/api.ts` (API configuration)
- [ ] Create `src/services/apiClient.ts` (Axios instance + methods)
- [ ] Create `src/hooks/useAgentAPI.ts` (React hooks for data fetching)

### Phase 3: Components
- [ ] Build `DashboardHeader` component
- [ ] Build `GeospatialView` component (with Mapbox)
- [ ] Build `AnalyticsView` component (with Recharts)
- [ ] Build `DataTableView` component
- [ ] Build `CopilorPanel` component

### Phase 4: Layout & Integration
- [ ] Create main `App` component with layout grid
- [ ] Wire components to API hooks
- [ ] Add loading states & error boundaries
- [ ] Implement auto-refresh logic

### Phase 5: Styling & Polish
- [ ] Apply design system colors (Orange/Blue theme)
- [ ] Add animations (fade-in, slide-in, pulse)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Accessibility improvements

### Phase 6: Testing & Deployment
- [ ] Unit tests for components
- [ ] Integration tests with backend
- [ ] E2E tests with test data
- [ ] Build Docker image for deployment

---

## 📈 Sample Data Structures

### Dashboard KPI Card
```json
{
  "label": "RRC Setup Success Rate",
  "value": "98.5%",
  "trend": "up",           // or "down" or "stable"
  "status": "success"      // or "warning" or "destructive"
}
```

### Cell for Map Popup
```json
{
  "cell_id": "cell_001",
  "status": "Optimal",           // or "Degraded" or "Critical"
  "load_percentage": 45,
  "rrc_success_rate": 98.5,
  "coordinates": [77.1025, 28.7041]
}
```

### Time-Series Data Point
```json
{
  "timestamp": "2025-10-20T12:00:00Z",
  "rrc_success_rate": 98.5,
  "handover_success_rate": 97.2,
  "throughput_mbps": 125.3
}
```

### Recommendation Card
```json
{
  "title": "Increase Antenna Tilt",
  "description": "Reduce interference on cells 001-005 by increasing antenna tilt angle",
  "impact": "Expected 3dB RSRP improvement, reduces handover failures by 2%",
  "actions": ["Approve", "Reject"]
}
```

---

## 🚀 Testing Backend APIs

### 1. Health Check
```bash
curl http://localhost:8080/ping
```

### 2. Get Dashboard KPIs
```bash
curl http://localhost:8080/api/dashboard/kpis | jq
```

### 3. Get Cell Status
```bash
curl http://localhost:8080/api/cells/status | jq
```

### 4. Get Time-Series Data
```bash
curl "http://localhost:8080/api/analytics/timeseries?hours=24" | jq
```

### 5. Get Cell Performance
```bash
curl http://localhost:8080/api/cells/performance | jq
```

### 6. Test Agent
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Are there any anomalies?"}}'
```

---

## 🎯 Design System Reference

### Colors (HSL-based CSS Variables)
```css
--color-primary: hsl(17, 88%, 48%);      /* Orange #ea580c */
--color-secondary: hsl(199, 89%, 48%);   /* Blue #0ea5e9 */
--color-success: hsl(160, 84%, 39%);     /* Green #10b981 */
--color-warning: hsl(45, 96%, 56%);      /* Amber #f59e0b */
--color-destructive: hsl(0, 84%, 60%);   /* Red #ef4444 */
```

### Status Colors
```
✅ Optimal/Success:    Green (#10b981)
⚠️  Degraded/Warning:  Amber (#f59e0b)
❌ Critical/Error:     Red (#ef4444)
```

### Animations
- Fade-in: 0.3s ease-in
- Slide-in: 0.4s ease-out
- Pulse: 2s infinite (for alerts)

---

## 📋 Component Specifications

### Dashboard Header Component
**Props**:
- `refreshInterval`: ms between refreshes (default: 30000)
- `onKPIClick`: callback when KPI card clicked

**State**:
- kpis: Object with RRC, Active Cells, Alarms, Load
- loading: Boolean
- error: String or null

### Geospatial View Component
**Props**:
- `initialCenter`: [longitude, latitude]
- `initialZoom`: Number
- `onCellClick`: callback with cell data
- `heatmapEnabled`: Boolean

**State**:
- cells: Array of cell objects
- heatmapData: GeoJSON FeatureCollection
- selectedCell: Cell object or null

### Analytics View Component
**Props**:
- `timeWindow`: Number of hours
- `metrics`: Array of metric names
- `refreshInterval`: ms between refreshes

**State**:
- data: Array of time-series points
- selectedMetric: String
- loading: Boolean

### Data Table Component
**Props**:
- `rows`: Array of cell performance objects
- `sortBy`: String (column name)
- `limit`: Number of rows

**State**:
- sortColumn: String
- sortOrder: 'asc' | 'desc'
- filtered: Boolean

### Co-pilot Panel Component
**Props**:
- `onRecommendationApprove`: callback
- `onRecommendationReject`: callback

**State**:
- messages: Array of message objects
- input: String
- loading: Boolean

---

## 🔄 Data Flow Diagram

```
User Interaction
      ↓
React Component (DashboardHeader)
      ↓
useAgentAPI Hook (useDashboardKPIs)
      ↓
APIClient Service (getDashboardKPIs)
      ↓
Axios HTTP Request (GET /api/dashboard/kpis)
      ↓
FastAPI Backend
      ├─ Checks AWS credentials
      ├─ Queries Athena (future) or returns mock data
      └─ Returns JSON response
      ↓
Frontend receives data
      ↓
Component re-renders with new data
      ↓
User sees updated UI
```

---

## 📝 Code Examples

### Using the API Hook in a Component

```tsx
import React from 'react';
import { useDashboardKPIs } from '../hooks/useAgentAPI';

export function Dashboard() {
  const { kpis, loading, error, refetch } = useDashboardKPIs(30000);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>System Status: {kpis.status}</h1>
      <button onClick={refetch}>Refresh Now</button>
      {/* Display KPI cards */}
    </div>
  );
}
```

### Sending Chat Message

```tsx
import { useAgentInvoke } from '../hooks/useAgentAPI';

export function ChatInput() {
  const [message, setMessage] = React.useState('');
  const { invoke, loading } = useAgentInvoke();

  const handleSend = async () => {
    const response = await invoke(message);
    console.log('Agent response:', response);
    setMessage('');
  };

  return (
    <div>
      <input 
        value={message} 
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask me anything..."
      />
      <button onClick={handleSend} disabled={loading}>
        {loading ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
}
```

---

## ✅ Completion Checklist

### Backend (✅ Complete)
- [x] Agent deployed to AgentCore Runtime
- [x] 13 tools integrated and working
- [x] 6 REST API endpoints implemented
- [x] CORS enabled
- [x] Mock data working
- [x] Error handling in place
- [x] Logging configured

### Frontend (⏳ In Progress)
- [ ] React app created
- [ ] API services implemented
- [ ] Components built
- [ ] Styling applied
- [ ] Testing completed
- [ ] Deployed

### Integration
- [ ] Backend & frontend communicating
- [ ] All endpoints working from UI
- [ ] Real-time updates (optional)
- [ ] Error handling working
- [ ] Performance optimized

---

## 📞 Support & Documentation

- **Backend API Docs**: See `src/agent/app.py`
- **Integration Guide**: See `docs/ui_frontend_integration.md`
- **Architecture**: See `docs/documentation.md`
- **Deployment**: See `README.md`

---

## 🎉 Next Steps

1. **UI Team**: Start building React components using the provided templates
2. **Backend Team**: Replace mock data with Athena queries when ready
3. **QA Team**: Test all endpoints end-to-end
4. **DevOps Team**: Configure production deployment settings
5. **Everyone**: Celebrate the progress! 🚀
