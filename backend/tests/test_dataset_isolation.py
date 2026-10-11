"""
Dataset Isolation and Session Integrity Test Suite.
Verifies that multiple datasets maintain strict isolation,
unknown dataset IDs are rejected with HTTP 404, and cross-session leakage cannot occur.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from main import app, DATASET_SESSIONS, ACTIVE_SESSION, _process_dataframe


@pytest.fixture
def two_distinct_datasets():
    """Create two distinct test datasets with unique metrics."""
    df_alpha = pd.DataFrame([
        {"order_id": "ORD-A1", "order_date": "2024-01-01", "customer_id": "C-1", "customer_segment": "Enterprise",
         "product_id": "P-1", "product_name": "Alpha Service", "category": "Cloud", "region": "North America",
         "quantity": 10, "unit_price": 100.0, "discount": 0.0, "revenue": 1000.0},
        {"order_id": "ORD-A2", "order_date": "2024-01-02", "customer_id": "C-2", "customer_segment": "Enterprise",
         "product_id": "P-1", "product_name": "Alpha Service", "category": "Cloud", "region": "North America",
         "quantity": 20, "unit_price": 100.0, "discount": 0.0, "revenue": 2000.0},
        {"order_id": "ORD-A3", "order_date": "2024-01-03", "customer_id": "C-3", "customer_segment": "Enterprise",
         "product_id": "P-1", "product_name": "Alpha Service", "category": "Cloud", "region": "North America",
         "quantity": 30, "unit_price": 100.0, "discount": 0.0, "revenue": 3000.0},
        {"order_id": "ORD-A4", "order_date": "2024-01-04", "customer_id": "C-4", "customer_segment": "Enterprise",
         "product_id": "P-1", "product_name": "Alpha Service", "category": "Cloud", "region": "North America",
         "quantity": 40, "unit_price": 100.0, "discount": 0.0, "revenue": 4000.0},
        {"order_id": "ORD-A5", "order_date": "2024-01-05", "customer_id": "C-5", "customer_segment": "Enterprise",
         "product_id": "P-1", "product_name": "Alpha Service", "category": "Cloud", "region": "North America",
         "quantity": 50, "unit_price": 100.0, "discount": 0.0, "revenue": 5000.0},
    ])  # Total Alpha: $15,000 across 5 orders

    df_beta = pd.DataFrame([
        {"order_id": "ORD-B1", "order_date": "2024-06-01", "customer_id": "C-9", "customer_segment": "SMB",
         "product_id": "P-9", "product_name": "Beta Gadget", "category": "Hardware", "region": "APAC",
         "quantity": 2, "unit_price": 50.0, "discount": 0.0, "revenue": 100.0},
        {"order_id": "ORD-B2", "order_date": "2024-06-02", "customer_id": "C-9", "customer_segment": "SMB",
         "product_id": "P-9", "product_name": "Beta Gadget", "category": "Hardware", "region": "APAC",
         "quantity": 4, "unit_price": 50.0, "discount": 0.0, "revenue": 200.0},
        {"order_id": "ORD-B3", "order_date": "2024-06-03", "customer_id": "C-9", "customer_segment": "SMB",
         "product_id": "P-9", "product_name": "Beta Gadget", "category": "Hardware", "region": "APAC",
         "quantity": 6, "unit_price": 50.0, "discount": 0.0, "revenue": 300.0},
        {"order_id": "ORD-B4", "order_date": "2024-06-04", "customer_id": "C-9", "customer_segment": "SMB",
         "product_id": "P-9", "product_name": "Beta Gadget", "category": "Hardware", "region": "APAC",
         "quantity": 8, "unit_price": 50.0, "discount": 0.0, "revenue": 400.0},
        {"order_id": "ORD-B5", "order_date": "2024-06-05", "customer_id": "C-9", "customer_segment": "SMB",
         "product_id": "P-9", "product_name": "Beta Gadget", "category": "Hardware", "region": "APAC",
         "quantity": 10, "unit_price": 50.0, "discount": 0.0, "revenue": 500.0},
    ])  # Total Beta: $1,500 across 5 orders

    res_alpha = _process_dataframe(df_alpha, filename="alpha.csv")
    res_beta = _process_dataframe(df_beta, filename="beta.csv")

    return res_alpha, res_beta


def test_sequential_datasets_distinct_ids(two_distinct_datasets):
    """Verify that two sequentially analyzed datasets have unique IDs and distinct metrics."""
    res_alpha, res_beta = two_distinct_datasets
    assert res_alpha.dataset_id != res_beta.dataset_id
    assert res_alpha.metrics.total_revenue == 15000.0
    assert res_beta.metrics.total_revenue == 1500.0


def test_ask_question_respects_dataset_id(two_distinct_datasets):
    """Ensure querying with dataset Alpha's ID uses Alpha's context, not Beta's context."""
    res_alpha, res_beta = two_distinct_datasets
    client = TestClient(app)

    with patch("main.answer_analytical_question") as mock_answer:
        mock_answer.side_effect = lambda q, analysis: {
            "answer": f"Revenue for {analysis.dataset_meta.filename} is ${analysis.metrics.total_revenue:,.2f}",
            "observed_facts": [f"Total: ${analysis.metrics.total_revenue:,.2f}"],
            "recommendations": [],
            "is_grounded": True,
            "model_used": "gemini-2.5-flash",
            "ai_configured": True,
        }

        # Query Alpha explicitly
        resp_a = client.post("/api/ask", json={
            "question": "What is revenue?",
            "dataset_id": res_alpha.dataset_id,
        })
        assert resp_a.status_code == 200
        assert "$15,000.00" in resp_a.json()["answer"]

        # Query Beta explicitly
        resp_b = client.post("/api/ask", json={
            "question": "What is revenue?",
            "dataset_id": res_beta.dataset_id,
        })
        assert resp_b.status_code == 200
        assert "$1,500.00" in resp_b.json()["answer"]


def test_unknown_dataset_id_returns_404():
    """Submitting an invalid, unknown, or expired dataset_id must return HTTP 404, not silent fallback."""
    client = TestClient(app)
    resp = client.post("/api/ask", json={
        "question": "What is total revenue?",
        "dataset_id": "ds-completely-unknown-999",
    })
    assert resp.status_code == 404
    assert "not found or has expired" in resp.json()["detail"]


def test_omitted_dataset_id_uses_active_session(two_distinct_datasets):
    """When dataset_id is omitted, it defaults to the latest active dataset."""
    _, res_beta = two_distinct_datasets  # res_beta was processed last, so it is active
    client = TestClient(app)

    with patch("main.answer_analytical_question") as mock_answer:
        mock_answer.side_effect = lambda q, analysis: {
            "answer": f"Active is {analysis.dataset_meta.filename}",
            "observed_facts": [],
            "recommendations": [],
            "is_grounded": True,
            "model_used": "gemini-2.5-flash",
            "ai_configured": True,
        }

        resp = client.post("/api/ask", json={"question": "What is active?"})
        assert resp.status_code == 200
        assert "beta.csv" in resp.json()["answer"]
