"""
tests/api/test_infer_server.py — FastAPI endpoint integration tests.
"""

import os
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import httpx
from inference.infer_server import app, state, REFLECTION_LOG

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def async_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.anyio
async def test_api_status_endpoint(async_client):
    """Test GET /api/status returns valid state dictionary."""
    async with async_client as client:
        response = await client.get("/api/status")
        assert response.status_code == 200
        json_data = response.json()
        assert "status" in json_data
        assert "deployments" in json_data

@pytest.mark.anyio
async def test_api_logs_download_endpoint(async_client, tmp_path):
    """Test GET /api/logs/download returns downloadable CSV file."""
    if not os.path.exists(REFLECTION_LOG):
        with open(REFLECTION_LOG, "w") as f:
            f.write("timestamp,deployment,actual_cpu,predicted_cpu_step1,current_replicas,recommended_replicas\n")

    async with async_client as client:
        response = await client.get("/api/logs/download")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

@pytest.mark.anyio
@patch("inference.infer_server.PrometheusClient")
async def test_api_accuracy_endpoint(mock_prom_class, async_client):
    """Test GET /api/accuracy merges actual and predicted data cleanly."""
    mock_prom = MagicMock()
    mock_prom_class.return_value = mock_prom

    now = datetime.now(timezone.utc)
    actual_df = pd.DataFrame({
        "timestamp": [now],
        "cpu": [0.45]
    })
    pred_df = pd.DataFrame({
        "timestamp": [now],
        "predicted": [0.48]
    })

    mock_prom.fetch_deployment_cpu_series.return_value = actual_df
    mock_prom.fetch_prediction_accuracy_series.return_value = pred_df

    state["deployments"] = {"stressor-app": {}}

    async with async_client as client:
        response = await client.get("/api/accuracy?horizon_minutes=5&display_minutes=60")
        assert response.status_code == 200
        data = response.json()
        assert "stressor-app" in data
        assert len(data["stressor-app"]) == 1
        assert data["stressor-app"][0]["actual"] == 0.45
        assert data["stressor-app"][0]["predicted"] == 0.48
