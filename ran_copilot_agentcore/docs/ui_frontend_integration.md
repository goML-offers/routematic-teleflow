# RAN Co-pilot Frontend Integration Guide

## Overview

The UI team has built a comprehensive React dashboard for RAN Co-pilot with four main components. This document outlines the architecture, data formats, and API integration points.

## Architecture

```
Frontend (React)
├── Dashboard Header (Global KPI Display)
├── Main Canvas (3 View Modes)
│   ├── Geospatial View (Mapbox)
│   ├── Analytics View (Recharts)
│   └── Data Table View
├── Co-pilot Panel (Chat Interface)
└── Design System (Orange/Blue theme)
    ↓
Backend APIs (Python FastAPI)
├── Agent Endpoint (/invocations)
├── KPI Data Endpoints
├── Cell Status Endpoints
└── Heatmap Data Endpoint (/get_heatmap_data)
```

## Component Details

### 1. Dashboard Header (Global KPI Display)

**Purpose**: Real-time network health at a glance

**Components**:
- System status indicator (Operational/Degraded/Critical)
- 4 KPI cards with:
  - Value display
  - Trend indicator (↑↓)
  - Status color (success/warning/destructive)

**KPI Cards**:
1. RRC Setup Success Rate (%)
2. Active Cells count
3. Critical Alarms count
4. Network Load (%)

**Color Coding**:
- Green: Optimal performance
- Amber: Degraded performance
- Red: Critical issues

### 2. Main Canvas Area (3 View Modes)

#### A. Geospatial View (Interactive Map)

**Library**: Mapbox GL JS

**Features**:
- **Static Cell Markers**: Color-coded by load percentage
  - Green: 0-60% load
  - Orange: 60-85% load
  - Red: 85%+ load
- **Interactive Pop-ups**: Show Cell ID, Status, Load %, GPS coordinates
- **Heatmap Layer**: KPI visualization as color gradient
- **Dynamic Legend**: Color gradient scale (Low/Medium/High)
- **Controls**: Zoom, pan, navigation

**Data Format - GeoJSON FeatureCollection**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [77.1025, 28.7041]  // [longitude, latitude]
      },
      "properties": {
        "cell_id": "cell_001",
        "value": -84.2,              // KPI numerical value
        "color": "#00FF00",          // Pre-calculated severity color
        "signal_strength": -84,      // For heatmap display
        "load_percentage": 45        // Optional: for marker coloring
      }
    }
  ]
}
```

**Props Accepted**:
- `heatmapData`: GeoJSON object
- `kpiName`: String for pop-up display (e.g., "RSRP Signal Strength")

#### B. Analytics View (Charts & Graphs)

**Library**: Recharts

**Chart Sections**:

1. **KPI Trends (Line Chart)**
   - Shows RRC Success Rate and Handover Success Rate over 24h
   - Dual Y-axis
   - Data format: `[{timestamp, rrc_rate, handover_rate}, ...]`

2. **Network Throughput (Area Chart)**
   - Displays throughput over 24h
   - Data format: `[{timestamp, throughput_mbps}, ...]`

3. **Alarm Distribution (Bar Chart)**
   - Alarm counts by type
   - Data format: `[{alarm_type: "Critical|Major|Minor|Warning", count}, ...]`

4. **AI Insights Card**
   - AI-generated insights
   - Trend indicator
   - Summary text

#### C. Data Table View

**Columns**:
- Cell ID
- RRC Success Rate (%)
- Handover Success Rate (%)
- Network Load (%)
- Active Alarms count
- Status badge (Optimal/Degraded/Critical)

**Data Format**:
```json
[
  {
    "cell_id": "cell_001",
    "rrc_success_rate": 98.5,
    "handover_success_rate": 97.2,
    "network_load": 45,
    "active_alarms": 2,
    "status": "Optimal"
  }
]
```

### 3. Co-pilot Panel (Chat Interface)

**Location**: Right sidebar (fixed width: 384px)

**Components**:
- Header: "RAN Co-pilot" with AI icon
- Message Display Area: Scrollable conversation history
- Recommendation Cards: Rich message type
- Input Area: Text input + Send button
- Timestamps on all messages

**Message Format**:
```json
{
  "role": "user|assistant",
  "content": "string",
  "timestamp": "2025-10-20T12:30:00Z",
  "recommendation": {
    "title": "Increase Antenna Tilt",
    "description": "Reduce interference on cell_001",
    "impact": "Expected 3dB RSRP improvement"
  }
}
```

**Special Features**:
- Differentiates user vs assistant messages
- Recommendation cards show action buttons (Approve/Reject)
- Inline links to related tools

### 4. Design System

**Color Palette**: Orange primary theme with blue/grey accents

**Semantic Tokens** (HSL-based CSS variables):
- Primary Orange: `#ea580c` (hsl(17, 88%, 48%))
- Secondary Blue: `#0ea5e9` (hsl(199, 89%, 48%))
- Success Green: `#10b981` (hsl(160, 84%, 39%))
- Warning Amber: `#f59e0b` (hsl(45, 96%, 56%))
- Destructive Red: `#ef4444` (hsl(0, 84%, 60%))

**Animations**:
- Fade-in effects
- Slide-in transitions
- Pulse effects for alerts

## Backend Integration Points

### Required APIs

#### 1. **Dashboard KPI API**
```
GET /api/dashboard/kpis
Response: {
  "rrc_success_rate": 98.5,
  "active_cells": 25,
  "critical_alarms": 3,
  "network_load": 62.5,
  "status": "Operational|Degraded|Critical"
}
```

#### 2. **Cell Status API**
```
GET /api/cells/status
Response: [
  {
    "cell_id": "cell_001",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "status": "Optimal|Degraded|Critical",
    "load_percentage": 45,
    "rrc_success_rate": 98.5
  }
]
```

#### 3. **Heatmap Data API**
```
POST /invocations
Body: {
  "input": {"prompt": "Generate heatmap for RSRP signal strength"}
}
Response: GeoJSON FeatureCollection (from get_heatmap_data tool)
```

#### 4. **Time-Series Data API**
```
GET /api/analytics/timeseries?metric=rrc_success_rate&hours=24
Response: [
  {
    "timestamp": "2025-10-20T12:00:00Z",
    "rrc_success_rate": 98.5,
    "handover_success_rate": 97.2,
    "throughput_mbps": 125.3
  }
]
```

#### 5. **Cell Performance API**
```
GET /api/cells/performance?limit=100
Response: [
  {
    "cell_id": "cell_001",
    "rrc_success_rate": 98.5,
    "handover_success_rate": 97.2,
    "network_load": 45,
    "active_alarms": 2,
    "status": "Optimal"
  }
]
```

#### 6. **Agent/Chat API**
```
POST /invocations
Body: {
  "input": {"prompt": "User's question or request"}
}
Response: {
  "output": {
    "message": {
      "role": "assistant",
      "content": "Agent's response",
      "recommendation": {...}  // Optional
    },
    "timestamp": "2025-10-20T12:30:00Z"
  }
}
```

#### 7. **WebSocket/Real-time Updates** (Optional)
```
WebSocket: ws://agent-endpoint/ws
Messages: Real-time KPI updates, alerts, recommendations
```

## Backend Implementation Status

### ✅ API Endpoints Now Available

All required endpoints are now implemented in the agent (`src/agent/app.py`):

1. **GET `/ping`** - Health check
2. **POST `/invocations`** - Main agent endpoint
3. **GET `/api/dashboard/kpis`** - Dashboard KPI data
4. **GET `/api/cells/status`** - Cell status and location data
5. **GET `/api/analytics/timeseries`** - Time-series KPI metrics
6. **GET `/api/cells/performance`** - Cell performance details
7. **CORS enabled** - Frontend can call from any origin (configurable)

### Current Implementation Status
- ✅ Mock data endpoints working
- ⏳ Integration with Athena - To be implemented
- ⏳ Real-time updates via WebSocket - To be implemented

---

## React Integration Guide

### 1. API Configuration

**File: `src/config/api.ts`** (Frontend)

```typescript
// API base URL - update based on your deployment
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

// API endpoints
export const API_ENDPOINTS = {
  PING: '/ping',
  INVOCATIONS: '/invocations',
  DASHBOARD_KPIs: '/api/dashboard/kpis',
  CELLS_STATUS: '/api/cells/status',
  ANALYTICS_TIMESERIES: '/api/analytics/timeseries',
  CELLS_PERFORMANCE: '/api/cells/performance',
};

// HTTP config
export const HTTP_CONFIG = {
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
};
```

### 2. API Client Service

**File: `src/services/apiClient.ts`** (Frontend)

```typescript
import axios, { AxiosInstance } from 'axios';
import { API_BASE_URL, HTTP_CONFIG, API_ENDPOINTS } from '../config/api';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  ...HTTP_CONFIG,
});

// Error interceptor
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error);
    throw error;
  }
);

// API Client
export const APIClient = {
  // Health check
  async ping() {
    return apiClient.get(API_ENDPOINTS.PING);
  },

  // Main agent invocation
  async invoke(prompt: string) {
    return apiClient.post(API_ENDPOINTS.INVOCATIONS, {
      input: { prompt },
    });
  },

  // Dashboard KPIs
  async getDashboardKPIs() {
    return apiClient.get(API_ENDPOINTS.DASHBOARD_KPIs);
  },

  // Cell status (for map)
  async getCellsStatus() {
    return apiClient.get(API_ENDPOINTS.CELLS_STATUS);
  },

  // Time-series analytics
  async getTimeseriesAnalytics(metric = 'rrc_success_rate', hours = 24) {
    return apiClient.get(API_ENDPOINTS.ANALYTICS_TIMESERIES, {
      params: { metric, hours },
    });
  },

  // Cell performance
  async getCellPerformance(limit = 100) {
    return apiClient.get(API_ENDPOINTS.CELLS_PERFORMANCE, {
      params: { limit },
    });
  },
};

export default APIClient;
```

### 3. React Hooks for Data Fetching

**File: `src/hooks/useAgentAPI.ts`** (Frontend)

```typescript
import { useState, useEffect, useCallback } from 'react';
import APIClient from '../services/apiClient';

// Dashboard KPI Hook
export function useDashboardKPIs(refreshInterval = 30000) {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchKPIs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await APIClient.getDashboardKPIs();
      setKpis(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKPIs();
    if (refreshInterval > 0) {
      const interval = setInterval(fetchKPIs, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchKPIs]);

  return { kpis, loading, error, refetch: fetchKPIs };
}

// Cell Status Hook
export function useCellsStatus(refreshInterval = 30000) {
  const [cells, setCells] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCells = useCallback(async () => {
    setLoading(true);
    try {
      const data = await APIClient.getCellsStatus();
      setCells(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCells();
    if (refreshInterval > 0) {
      const interval = setInterval(fetchCells, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchCells]);

  return { cells, loading, error, refetch: fetchCells };
}

// Time-Series Analytics Hook
export function useTimeseriesAnalytics(metric = 'rrc_success_rate', hours = 24) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await APIClient.getTimeseriesAnalytics(metric, hours);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [metric, hours]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Cell Performance Hook
export function useCellPerformance(limit = 100) {
  const [cells, setCells] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPerformance = useCallback(async () => {
    setLoading(true);
    try {
      const data = await APIClient.getCellPerformance(limit);
      setCells(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchPerformance();
  }, [fetchPerformance]);

  return { cells, loading, error, refetch: fetchPerformance };
}

// Agent Invocation Hook
export function useAgentInvoke() {
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const invoke = useCallback(async (prompt) => {
    setLoading(true);
    try {
      const result = await APIClient.invoke(prompt);
      setResponse(result);
      setError(null);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { response, loading, error, invoke };
}
```

### 4. Component Integration Examples

#### Dashboard Header Component

**File: `src/components/DashboardHeader.tsx`** (Frontend)

```typescript
import React from 'react';
import { useDashboardKPIs } from '../hooks/useAgentAPI';

interface KPICardProps {
  label: string;
  value: number | string;
  trend?: 'up' | 'down' | 'stable';
  status?: 'success' | 'warning' | 'destructive';
}

const KPICard: React.FC<KPICardProps> = ({ label, value, trend, status }) => (
  <div className={`kpi-card status-${status}`}>
    <div className="kpi-label">{label}</div>
    <div className="kpi-value">{value}</div>
    {trend && <div className="kpi-trend">{trend === 'up' ? '↑' : '↓'}</div>}
  </div>
);

export const DashboardHeader: React.FC = () => {
  const { kpis, loading, error } = useDashboardKPIs(30000); // Refresh every 30s

  if (loading) return <div>Loading KPIs...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!kpis) return <div>No data</div>;

  // Determine status colors
  const getStatusColor = (kpi: string, value: number) => {
    if (kpi === 'rrc_success_rate') {
      if (value >= 95) return 'success';
      if (value >= 90) return 'warning';
      return 'destructive';
    }
    if (kpi === 'network_load') {
      if (value <= 60) return 'success';
      if (value <= 85) return 'warning';
      return 'destructive';
    }
    return 'success';
  };

  return (
    <div className="dashboard-header">
      <div className="system-status">
        Status: <span className={`status-${kpis.status}`}>{kpis.status}</span>
      </div>
      <div className="kpi-grid">
        <KPICard
          label="RRC Setup Success Rate"
          value={`${kpis.rrc_success_rate}%`}
          status={getStatusColor('rrc_success_rate', kpis.rrc_success_rate)}
        />
        <KPICard
          label="Active Cells"
          value={kpis.active_cells}
          status="success"
        />
        <KPICard
          label="Critical Alarms"
          value={kpis.critical_alarms}
          status={kpis.critical_alarms > 5 ? 'destructive' : 'success'}
        />
        <KPICard
          label="Network Load"
          value={`${kpis.network_load}%`}
          status={getStatusColor('network_load', kpis.network_load)}
        />
      </div>
    </div>
  );
};
```

#### Geospatial Map Component

**File: `src/components/GeospatialView.tsx`** (Frontend)

```typescript
import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import { useCellsStatus } from '../hooks/useAgentAPI';

export const GeospatialView: React.FC = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const { cells, loading } = useCellsStatus(30000);

  useEffect(() => {
    if (!mapContainer.current) return;

    // Initialize map
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [77.1025, 28.7041], // Default to Delhi
      zoom: 10,
    });

    map.current.on('load', () => {
      // Add cell markers source
      map.current.addSource('cells', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [],
        },
      });

      // Add circle layer for cells
      map.current.addLayer({
        id: 'cells-circle',
        type: 'circle',
        source: 'cells',
        paint: {
          'circle-radius': 8,
          'circle-color': [
            'case',
            ['==', ['get', 'status'], 'Critical'],
            '#ef4444', // Red
            ['==', ['get', 'status'], 'Degraded'],
            '#f59e0b', // Amber
            '#10b981', // Green
          ],
          'circle-opacity': 0.8,
        },
      });

      // Add popup on click
      map.current.on('click', 'cells-circle', (e) => {
        const properties = e.features[0].properties;
        new mapboxgl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(
            `<div>
              <h3>${properties.cell_id}</h3>
              <p>Status: ${properties.status}</p>
              <p>Load: ${properties.load_percentage}%</p>
              <p>RRC: ${properties.rrc_success_rate}%</p>
            </div>`
          )
          .addTo(map.current);
      });
    });

    return () => map.current?.remove();
  }, []);

  // Update markers when cells change
  useEffect(() => {
    if (!map.current || loading || !cells.length) return;

    const geojsonData = {
      type: 'FeatureCollection',
      features: cells.map(cell => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [cell.longitude, cell.latitude],
        },
        properties: {
          cell_id: cell.cell_id,
          status: cell.status,
          load_percentage: cell.load_percentage,
          rrc_success_rate: cell.rrc_success_rate,
        },
      })),
    };

    const source = map.current.getSource('cells');
    if (source) {
      source.setData(geojsonData);
    }
  }, [cells, loading]);

  return <div ref={mapContainer} style={{ width: '100%', height: '500px' }} />;
};
```

#### Co-pilot Chat Component

**File: `src/components/CopilorPanel.tsx`** (Frontend)

```typescript
import React, { useState, useRef, useEffect } from 'react';
import { useAgentInvoke } from '../hooks/useAgentAPI';

export const CopilorPanel: React.FC = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const { invoke, loading } = useAgentInvoke();
  const messagesEndRef = useRef(null);

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      // Invoke agent
      const response = await invoke(input);
      
      // Extract response content
      const assistantMessage = {
        role: 'assistant',
        content: response.output?.message?.content || 'No response',
        timestamp: new Date().toISOString(),
        recommendation: response.output?.message?.recommendation,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Agent invocation failed:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, an error occurred while processing your request.',
        timestamp: new Date().toISOString(),
      }]);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="copilot-panel">
      <div className="copilot-header">
        <h2>RAN Co-pilot</h2>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-content">{msg.content}</div>
            {msg.recommendation && (
              <div className="recommendation-card">
                <h4>{msg.recommendation.title}</h4>
                <p>{msg.recommendation.description}</p>
                <p className="impact">Impact: {msg.recommendation.impact}</p>
                <div className="action-buttons">
                  <button className="btn-approve">Approve</button>
                  <button className="btn-reject">Reject</button>
                </div>
              </div>
            )}
            <small className="message-timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </small>
          </div>
        ))}
        {loading && <div className="message-loading">Agent is thinking...</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask me anything about your RAN..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
};
```

### 5. Environment Variables

**File: `.env.local`** (Frontend)

```env
# Agent API Configuration
REACT_APP_API_URL=http://localhost:8080

# Optional: For production deployment
# REACT_APP_API_URL=https://agent.example.com

# Mapbox token (if using Mapbox)
REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
```

### 6. Build & Deployment

#### Deploy to Production

```bash
# Build frontend
cd frontend
npm run build

# The frontend will connect to REACT_APP_API_URL
# Make sure CORS is properly configured in the backend
```

#### Docker Deployment

**File: `Dockerfile.frontend`** (Frontend)

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG REACT_APP_API_URL=http://localhost:8080
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/build ./build
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]
```

Build and push:

```bash
docker build \
  --build-arg REACT_APP_API_URL=https://agent.example.com \
  -t your-registry/ran-copilot-frontend:latest \
  -f Dockerfile.frontend .

docker push your-registry/ran-copilot-frontend:latest
```

---

## Testing the Integration

### 1. Health Check

```bash
curl http://localhost:8080/ping
# Expected response: {"status": "healthy", "timestamp": "2025-10-20T..."}
```

### 2. Test Agent Invocation

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "Are there any performance anomalies?"}}'
```

### 3. Test Dashboard KPIs

```bash
curl http://localhost:8080/api/dashboard/kpis
```

### 4. Test Cell Status

```bash
curl http://localhost:8080/api/cells/status
```

### 5. Test Time-Series Data

```bash
curl "http://localhost:8080/api/analytics/timeseries?metric=rrc_success_rate&hours=24"
```

---

## Next Steps for UI Team

1. **Clone the integration code** - Copy the React components and hooks above
2. **Install dependencies** - `npm install axios mapbox-gl`
3. **Configure environment** - Set `REACT_APP_API_URL` in `.env.local`
4. **Test locally** - Start both backend and frontend on localhost
5. **Implement styling** - Apply the design system colors and animations
6. **Add error boundaries** - Wrap components with error handling
7. **Implement real-time updates** - Add WebSocket support when needed
8. **Deploy** - Use Docker or your preferred hosting platform

---

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
- ✅ Already fixed in the backend with `CORSMiddleware`
- In production, update `allow_origins` to specific domains

### 404 Not Found
- Make sure the backend is running on port 8080
- Check that `REACT_APP_API_URL` is correctly set
- Verify endpoint paths match exactly

### Slow API Responses
- Dashboard endpoints currently return mock data
- When integrated with Athena, add caching to improve performance
- Consider implementing pagination for large datasets

---
