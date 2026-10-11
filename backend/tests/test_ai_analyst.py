"""
Unit and Integration Test Suite for AI Analyst grounding and /api/ask endpoint.
All external Gemini calls are mocked in automated testing to avoid paid API calls.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from main import app, ACTIVE_SESSION, DATASET_SESSIONS
from models.schemas import (
    AnalysisResponse,
    DatasetMeta,
    DataQualityReport,
    CoreMetrics,
    MonthlyTrend,
    TopProduct,
    RegionalPerformance,
    AutomatedInsight,
)
from services.ai_analyst import (
    build_grounded_context,
    answer_analytical_question,
)


@pytest.fixture
def mock_analysis_response():
    """Build a deterministic AnalysisResponse fixture."""
    return AnalysisResponse(
        dataset_id="test-ds-123",
        dataset_meta=DatasetMeta(
            filename="test_sales.csv",
            row_count=1000,
            column_count=12,
            date_range={"start": "2024-01-01", "end": "2024-12-31"},
        ),
        data_quality=DataQualityReport(
            completeness_score=99.8,
            duplicate_rows=0,
            columns_profile=[],
            validation_status="valid",
            validation_notes=[],
        ),
        metrics=CoreMetrics(
            total_revenue=2500000.0,
            total_orders=500,
            average_order_value=5000.0,
            total_units_sold=7500,
            average_discount=0.08,
        ),
        monthly_trends=[
            MonthlyTrend(month="2024-01", revenue=180000.0, order_count=35, mom_growth_pct=None),
            MonthlyTrend(month="2024-02", revenue=220000.0, order_count=42, mom_growth_pct=22.2),
        ],
        top_products=[
            TopProduct(
                product_id="PRD-1",
                product_name="Apex Cloud Server",
                category="Infrastructure",
                revenue=750000.0,
                units_sold=600,
                share_of_total_pct=30.0,
            )
        ],
        regional_performance=[
            RegionalPerformance(
                region="North America",
                revenue=1250000.0,
                order_count=250,
                aov=5000.0,
                share_of_total_pct=50.0,
            ),
            RegionalPerformance(
                region="EMEA",
                revenue=750000.0,
                order_count=150,
                aov=5000.0,
                share_of_total_pct=30.0,
            ),
        ],
        top5_revenue_concentration_pct=65.0,
        automated_insights=[
            AutomatedInsight(
                id="peak-month",
                category="performance",
                title="Peak Revenue Month",
                description="Revenue peaked in Feb at $220k.",
                metric_reference="$220,000",
            )
        ],
        preview_rows=[],
    )


def test_build_grounded_context_contains_summaries_not_raw_csv(mock_analysis_response):
    """Ensure context builder compresses verified calculations and never includes raw CSV rows."""
    context = build_grounded_context(mock_analysis_response)

    # Must contain verified summary figures
    assert "$2,500,000.00" in context
    assert "North America" in context
    assert "Apex Cloud Server" in context
    assert "99.8%" in context

    # Must not contain raw row transaction headers or dumps
    assert "ORD-2024" not in context
    assert "CUST-" not in context
    assert "=== VERIFIED ANALYTICAL CONTEXT ===" in context


def test_missing_api_key_graceful_fallback(mock_analysis_response):
    """When GEMINI_API_KEY is unset, AI analyst returns a structured fallback without crashing."""
    with patch("services.ai_analyst.GEMINI_API_KEY", ""):
        res = answer_analytical_question("What is our revenue?", mock_analysis_response)
        assert res.ai_configured is False
        assert "GEMINI_API_KEY" in res.answer
        assert len(res.observed_facts) > 0


def test_empty_question_validation(mock_analysis_response):
    """Empty or whitespace-only questions must be cleanly caught."""
    res = answer_analytical_question("   ", mock_analysis_response)
    assert "provide a specific analytical question" in res.answer
    assert res.is_grounded is False


def test_question_too_long_validation(mock_analysis_response):
    """Questions exceeding 500 characters must be rejected."""
    long_question = "What is " + ("x" * 510)
    res = answer_analytical_question(long_question, mock_analysis_response)
    assert "exceeds maximum allowable length" in res.answer


def test_successful_mocked_gemini_call(mock_analysis_response):
    """Test standard successful analytical Q&A with mocked Gemini client."""
    mock_client = MagicMock()
    mock_gen_response = MagicMock()
    mock_gen_response.text = (
        '{"answer": "North America is the top market generating $1.25M (50% of revenue).", '
        '"observed_facts": ["North America: $1,250,000.00 (50.0% share)", "AOV: $5,000.00"], '
        '"recommendations": ["Investigate customer concentration in North America."]}'
    )
    mock_client.models.generate_content.return_value = mock_gen_response

    res = answer_analytical_question(
        "Which region generates the most revenue?",
        mock_analysis_response,
        client=mock_client,
    )

    assert "North America is the top market" in res.answer
    assert len(res.observed_facts) == 2
    assert "North America: $1,250,000.00 (50.0% share)" in res.observed_facts
    assert len(res.recommendations) == 1
    assert res.is_grounded is True
    assert res.ai_configured is True


def test_unanswerable_question_handling(mock_analysis_response):
    """Verify handling when the prompt asks for metrics outside the dataset (e.g. employee headcount)."""
    mock_client = MagicMock()
    mock_gen_response = MagicMock()
    mock_gen_response.text = (
        '{"answer": "This cannot be determined from the available dataset calculations.", '
        '"observed_facts": ["The dataset only covers sales transactions and revenue."], '
        '"recommendations": ["Integrate HR or headcount data to answer this query."]}'
    )
    mock_client.models.generate_content.return_value = mock_gen_response

    res = answer_analytical_question(
        "How many sales reps do we have?",
        mock_analysis_response,
        client=mock_client,
    )

    assert "cannot be determined" in res.answer


def test_gemini_api_timeout_and_failure(mock_analysis_response):
    """When Gemini raises a connection or timeout error, return a clear error response."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Deadline exceeded connecting to Gemini endpoint")

    res = answer_analytical_question(
        "Summarize monthly revenue",
        mock_analysis_response,
        client=mock_client,
    )

    assert res.is_grounded is False
    assert "Deadline exceeded" in res.answer
    assert "GEMINI_API_KEY and network connection" in res.recommendations[0]


def test_api_ask_endpoint_no_active_dataset():
    """Calling POST /api/ask without a loaded dataset must return HTTP 400."""
    client = TestClient(app)
    # Clear active session
    ACTIVE_SESSION["response"] = None
    ACTIVE_SESSION["dataset_id"] = None
    DATASET_SESSIONS.clear()

    resp = client.post("/api/ask", json={"question": "What is total revenue?"})
    assert resp.status_code == 400
    assert "No active dataset" in resp.json()["detail"]


def test_api_ask_endpoint_with_active_dataset(mock_analysis_response):
    """Calling POST /api/ask with an active dataset returns typed AskQuestionResponse."""
    client = TestClient(app)
    ACTIVE_SESSION["response"] = mock_analysis_response
    ACTIVE_SESSION["dataset_id"] = mock_analysis_response.dataset_id
    DATASET_SESSIONS[mock_analysis_response.dataset_id] = mock_analysis_response

    with patch("services.ai_analyst.answer_analytical_question") as mock_answer:
        mock_answer.return_value = {
            "answer": "Total revenue is $2,500,000.00 across 500 completed orders.",
            "observed_facts": ["Total Revenue: $2,500,000.00"],
            "recommendations": ["Review product concentration."],
            "is_grounded": True,
            "model_used": "gemini-2.5-flash",
            "ai_configured": True,
        }

        resp = client.post("/api/ask", json={
            "question": "What is our total revenue?",
            "dataset_id": mock_analysis_response.dataset_id,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "$2,500,000.00" in body["answer"]
        assert body["is_grounded"] is True


def test_api_ai_status_endpoint():
    """Calling GET /api/ai/status returns configuration status."""
    client = TestClient(app)
    resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "configured" in body
    assert "model" in body
