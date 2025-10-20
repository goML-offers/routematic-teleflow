# RAN Co-pilot API Documentation

## 1. Overview

This document provides the technical specifications for the RAN Co-pilot's backend API. This service provides endpoints for:
-   Retrieving network KPI data for dashboards and analytics.
-   Proxying chat requests to the AWS Bedrock agent for conversational AI capabilities.

## 2. Base URL

-   **Local Development**: `http://localhost:8080`
-   **Production**: The production URL will be provided upon deployment.

## 3. Authentication

No authentication is required for these endpoints at this time.

---

## 4. Health Check

### GET /ping

A simple health check to confirm the API service is running and healthy.

-   **Method**: `GET`
-   **Path**: `/ping`
-   **Request**: No body or parameters.
-   **Success Response (200 OK)**:
    ```json
    {
      "status": "healthy",
      "timestamp": "2023-10-21T10:00:00.123456+00:00"
    }
    ```

---

## 5. Dashboard & Analytics API Endpoints

### GET /api/dashboard/kpis

Retrieves the main Key Performance Indicators (KPIs) for the dashboard header.

-   **Method**: `GET`
-   **Path**: `/api/dashboard/kpis`
-   **Success Response (200 OK)**:
    ```json
    {
      "rrc_success_rate": 98.7,
      "active_cells": 75,
      "critical_alarms": 3,
      "network_load": 65.2,
      "status": "Operational"
    }
    ```

### GET /api/cells/status

Gets the status, load, and geographical coordinates for cell towers, primarily for display on the geospatial map.

-   **Method**: `GET`
-   **Path**: `/api/cells/status`
-   **Success Response (200 OK)**: An array of cell status objects.
    ```json
    [
      {
        "cell_id": "cell_001",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "status": "Optimal",
        "load_percentage": 55.5,
        "rrc_success_rate": 99.1
      },
      {
        "cell_id": "cell_002",
        "latitude": 34.0533,
        "longitude": -118.2448,
        "status": "Degraded",
        "load_percentage": 75.2,
        "rrc_success_rate": 92.5
      }
    ]
    ```

### GET /api/kpi/heatmap

Retrieves data formatted as a GeoJSON FeatureCollection, suitable for rendering a heatmap layer on the map.

-   **Method**: `GET`
-   **Path**: `/api/kpi/heatmap`
-   **Query Parameters**:
    -   `kpi_name` (string, optional, default: `throughput_mbps`): The name of the KPI to use for the heatmap values (e.g., `rrc_success_rate`, `network_load`).
-   **Success Response (200 OK)**:
    ```json
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [-118.2437, 34.0522]
          },
          "properties": {
            "kpi_value": 150.75
          }
        }
      ]
    }
    ```

### GET /api/analytics/timeseries

Retrieves time-series data for the analytics charts.

-   **Method**: `GET`
-   **Path**: `/api/analytics/timeseries`
-   **Query Parameters**:
    -   `hours` (integer, optional, default: 24): The number of past hours to retrieve data for.
-   **Success Response (200 OK)**: An array of data points.
    ```json
    [
      {
        "timestamp": "2023-10-21 09:00:00",
        "rrc_success_rate": 98.5,
        "handover_success_rate": 99.1,
        "throughput_mbps": 120.5
      },
      {
        "timestamp": "2023-10-21 10:00:00",
        "rrc_success_rate": 98.6,
        "handover_success_rate": 99.2,
        "throughput_mbps": 125.0
      }
    ]
    ```

### GET /api/cells/performance

Gets a detailed list of performance metrics for each cell, suitable for a data table.

-   **Method**: `GET`
-   **Path**: `/api/cells/performance`
-   **Query Parameters**:
    -   `limit` (integer, optional, default: 100): The maximum number of cells to return.
-   **Success Response (200 OK)**: An array of cell performance objects.
    ```json
    [
      {
        "cell_id": "cell_001",
        "rrc_success_rate": 99.1,
        "handover_success_rate": 99.5,
        "network_load": 55.5,
        "active_alarms": 0,
        "status": "Optimal"
      }
    ]
    ```

---

## 6. Agent Chat API

### POST /api/agent/invoke

Sends a user's prompt to the Bedrock agent and gets a response. It manages the conversation session automatically.

-   **Method**: `POST`
-   **Path**: `/api/agent/invoke`
-   **Request Body**:
    ```json
    {
      "prompt": "Hello, can you tell me about cells with degraded performance?",
      "sessionId": "optional-session-id-to-continue-a-conversation"
    }
    ```
-   **Success Response (200 OK)**:
    ```json
    {
      "completion": "Yes, I found three cells with degraded performance: cell_002, cell_005, and cell_009. The primary issue appears to be a low RRC success rate.",
      "sessionId": "new-or-existing-session-id"
    }
    ```

---

## 7. Error Handling

If an internal server error occurs (e.g., cannot connect to Athena, Bedrock agent is not configured), the API will return a `500 Internal Server Error` with a JSON body describing the issue.

-   **Example Error Response**:
    ```json
    {
      "detail": "Database query failed: Athena query failed: TABLE_NOT_FOUND: line 8:15: Table 'analytics_ue_metrics' not found."
    }
    ```
