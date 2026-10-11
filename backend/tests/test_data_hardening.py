"""
Data Hardening and CSV Ingestion Edge Case Test Suite.
Tests non-numeric string formatting ($ and commas), derived revenues,
malformed dates, edge case inputs, and upload validation constraints.
"""

import io
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from main import app, sanitize_dataframe, _cache_session, DATASET_SESSIONS, MAX_CACHED_SESSIONS
from services.analytics_engine import run_full_analytics


def test_sanitize_currency_and_commas():
    """Verify that strings with $, commas, percentages, and whitespace are cleanly converted."""
    raw_df = pd.DataFrame([
        {"revenue": "$1,250.50", "quantity": " 10 ", "unit_price": "$125.05", "discount": " 5% "},
        {"revenue": "$2,500.00", "quantity": "20", "unit_price": "$125.00", "discount": "10%"},
    ])
    cleaned = sanitize_dataframe(raw_df)

    assert cleaned["revenue"].iloc[0] == 1250.50
    assert cleaned["revenue"].iloc[1] == 2500.00
    assert cleaned["quantity"].iloc[0] == 10
    assert cleaned["quantity"].iloc[1] == 20
    assert cleaned["discount"].iloc[0] == 0.05
    assert cleaned["discount"].iloc[1] == 0.10


def test_derive_revenue_when_omitted():
    """Verify that when revenue column is omitted, it is derived deterministically from qty * price * (1-discount)."""
    raw_df = pd.DataFrame([
        {"quantity": 5, "unit_price": 200.0, "discount": 0.10},  # 5 * 200 * 0.9 = 900.0
        {"quantity": 10, "unit_price": 100.0, "discount": 0.00}, # 10 * 100 * 1.0 = 1000.0
    ])
    cleaned = sanitize_dataframe(raw_df)

    assert "revenue" in cleaned.columns
    assert cleaned["revenue"].iloc[0] == 900.0
    assert cleaned["revenue"].iloc[1] == 1000.0


from services.data_profiler import validate_dataset_schema


def test_negative_values_preserved_and_flagged_by_profiler():
    """Ensure negative values (e.g. returns/refunds) are preserved without silent alteration and flagged by the profiler."""
    raw_df = pd.DataFrame([
        {"revenue": -500.0, "quantity": 1, "unit_price": 10.0, "discount": 0.0},
        {"revenue": 1000.0, "quantity": 2, "unit_price": 500.0, "discount": 0.0},
    ])
    cleaned = sanitize_dataframe(raw_df)
    # Financial data is preserved faithfully, not silently clipped
    assert cleaned["revenue"].iloc[0] == -500.0
    assert cleaned["revenue"].iloc[1] == 1000.0

    # Profiler detects and flags the negative revenue condition
    status, notes = validate_dataset_schema(cleaned)
    assert status == "warning"
    assert any("negative revenue values" in n for n in notes)


def test_extra_columns_and_unusual_column_order():
    """Verify that datasets with unexpected extra columns and reversed column order process normally."""
    client = TestClient(app)
    csv_content = (
        "notes,region,discount,unit_price,quantity,extra_id,product_name,order_date,order_id\n"
        "note1,EMEA,0.0,100.0,2,X99,Product A,2024-01-01,ORD-1\n"
        "note2,EMEA,0.0,200.0,3,X98,Product B,2024-01-02,ORD-2\n"
        "note3,APAC,0.0,300.0,1,X97,Product A,2024-01-03,ORD-3\n"
        "note4,APAC,0.0,400.0,2,X96,Product C,2024-01-04,ORD-4\n"
        "note5,EMEA,0.0,500.0,1,X95,Product B,2024-01-05,ORD-5\n"
    )

    resp = client.post("/api/upload", files={"file": ("unusual_order.csv", csv_content.encode("utf-8"), "text/csv")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dataset_meta"]["row_count"] == 5
    assert body["metrics"]["total_revenue"] == 2*(100) + 3*(200) + 1*(300) + 2*(400) + 1*(500)  # 200 + 600 + 300 + 800 + 500 = 2400.0


def test_session_cache_bounding_lru():
    """Verify that session storage does not grow unbounded by testing LRU eviction at MAX_CACHED_SESSIONS."""
    from models.schemas import AnalysisResponse, DatasetMeta, DataQualityReport, CoreMetrics

    dummy_analysis = AnalysisResponse(
        dataset_id="dummy",
        dataset_meta=DatasetMeta(filename="d.csv", row_count=10, column_count=5, date_range=None),
        data_quality=DataQualityReport(completeness_score=100.0, duplicate_rows=0, columns_profile=[], validation_status="valid", validation_notes=[]),
        metrics=CoreMetrics(total_revenue=100.0, total_orders=1, average_order_value=100.0, total_units_sold=1, average_discount=0.0),
        monthly_trends=[],
        top_products=[],
        regional_performance=[],
        top5_revenue_concentration_pct=0.0,
        automated_insights=[],
        preview_rows=[],
    )

    DATASET_SESSIONS.clear()
    for i in range(MAX_CACHED_SESSIONS + 10):
        _cache_session(f"ds-{i}", dummy_analysis)

    # Must be capped at MAX_CACHED_SESSIONS
    assert len(DATASET_SESSIONS) == MAX_CACHED_SESSIONS
    # Oldest entries (ds-0 to ds-9) must have been evicted
    assert "ds-0" not in DATASET_SESSIONS
    assert f"ds-{MAX_CACHED_SESSIONS + 9}" in DATASET_SESSIONS
