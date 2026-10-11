"""
Verification and Test Suite for InsightDesk Phase 1.
Verifies all analytical computations against independently derived ground truths,
tests data profiling, and validates FastAPI endpoints.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from main import app
from core.config import SAMPLE_CSV_PATH
from sample_data.generate_sample_data import generate_b2b_sales_data
from services.analytics_engine import (
    compute_core_metrics,
    compute_monthly_trends,
    compute_top_products,
    compute_regional_performance,
    compute_top_concentration,
    run_full_analytics,
)
from services.data_profiler import profile_dataset, validate_dataset_schema
from services.insight_generator import generate_automated_insights


@pytest.fixture
def synthetic_test_df():
    """A compact, mathematically verified test dataframe."""
    records = [
        {"order_id": "ORD-1", "order_date": "2024-01-10", "customer_id": "C-1", "customer_segment": "Enterprise",
         "product_id": "P-1", "product_name": "Apex Server", "category": "Cloud", "region": "North America",
         "quantity": 2, "unit_price": 1000.00, "discount": 0.10, "revenue": 1800.00},
        {"order_id": "ORD-1", "order_date": "2024-01-10", "customer_id": "C-1", "customer_segment": "Enterprise",
         "product_id": "P-2", "product_name": "Sentrix Security", "category": "Security", "region": "North America",
         "quantity": 1, "unit_price": 500.00, "discount": 0.00, "revenue": 500.00},
        {"order_id": "ORD-2", "order_date": "2024-01-20", "customer_id": "C-2", "customer_segment": "Mid-Market",
         "product_id": "P-1", "product_name": "Apex Server", "category": "Cloud", "region": "EMEA",
         "quantity": 1, "unit_price": 1000.00, "discount": 0.00, "revenue": 1000.00},
        {"order_id": "ORD-3", "order_date": "2024-02-05", "customer_id": "C-3", "customer_segment": "Small Business",
         "product_id": "P-3", "product_name": "DevWorkspace IDE", "category": "Dev Tools", "region": "APAC",
         "quantity": 10, "unit_price": 100.00, "discount": 0.20, "revenue": 800.00},
        {"order_id": "ORD-4", "order_date": "2024-02-18", "customer_id": "C-4", "customer_segment": "Enterprise",
         "product_id": "P-2", "product_name": "Sentrix Security", "category": "Security", "region": "North America",
         "quantity": 2, "unit_price": 500.00, "discount": 0.10, "revenue": 900.00},
    ]
    return pd.DataFrame(records)


def test_core_metrics_ground_truth(synthetic_test_df):
    """Verify that core KPIs match manual arithmetic exactly."""
    metrics = compute_core_metrics(synthetic_test_df)
    
    # Independent ground truths
    # Revenues: 1800 + 500 + 1000 + 800 + 900 = 5000.00
    expected_revenue = 5000.00
    # Orders: ORD-1, ORD-2, ORD-3, ORD-4 = 4 unique orders
    expected_orders = 4
    # AOV: 5000.00 / 4 = 1250.00
    expected_aov = 1250.00
    # Units: 2 + 1 + 1 + 10 + 2 = 16
    expected_units = 16
    # Discounts: (0.10 + 0.00 + 0.00 + 0.20 + 0.10) / 5 = 0.08
    expected_discount = 0.08

    assert metrics["total_revenue"] == pytest.approx(expected_revenue, rel=1e-4)
    assert metrics["total_orders"] == expected_orders
    assert metrics["average_order_value"] == pytest.approx(expected_aov, rel=1e-4)
    assert metrics["total_units_sold"] == expected_units
    assert metrics["average_discount"] == pytest.approx(expected_discount, rel=1e-4)


def test_monthly_trends_ground_truth(synthetic_test_df):
    """Verify monthly aggregation and MoM growth calculation."""
    trends = compute_monthly_trends(synthetic_test_df)
    
    assert len(trends) == 2
    # Jan 2024: ORD-1 ($2300) + ORD-2 ($1000) = $3300.00, 2 orders
    assert trends[0]["month"] == "2024-01"
    assert trends[0]["revenue"] == 3300.00
    assert trends[0]["order_count"] == 2
    assert trends[0]["mom_growth_pct"] is None  # Baseline month has no prior

    # Feb 2024: ORD-3 ($800) + ORD-4 ($900) = $1700.00, 2 orders
    # MoM: (1700 - 3300) / 3300 = -48.4848... -> -48.48%
    assert trends[1]["month"] == "2024-02"
    assert trends[1]["revenue"] == 1700.00
    assert trends[1]["order_count"] == 2
    assert trends[1]["mom_growth_pct"] == pytest.approx(-48.48, rel=1e-2)


def test_top_products_ranking(synthetic_test_df):
    """Verify ranking, unit sum, and share calculation."""
    top_prods = compute_top_products(synthetic_test_df)
    
    # P-1: 1800 + 1000 = 2800 (56.0% share), 3 units
    # P-2: 500 + 900 = 1400 (28.0% share), 3 units
    # P-3: 800 = 800 (16.0% share), 10 units
    assert len(top_prods) == 3
    assert top_prods[0]["product_id"] == "P-1"
    assert top_prods[0]["revenue"] == 2800.00
    assert top_prods[0]["share_of_total_pct"] == 56.00
    assert top_prods[0]["units_sold"] == 3

    assert top_prods[1]["product_id"] == "P-2"
    assert top_prods[1]["revenue"] == 1400.00
    assert top_prods[1]["share_of_total_pct"] == 28.00

    assert top_prods[2]["product_id"] == "P-3"
    assert top_prods[2]["revenue"] == 800.00
    assert top_prods[2]["share_of_total_pct"] == 16.00


def test_regional_performance_ground_truth(synthetic_test_df):
    """Verify regional grouping, AOV, and share %."""
    regional = compute_regional_performance(synthetic_test_df)
    
    # North America: ORD-1 ($2300) + ORD-4 ($900) = $3200, 2 orders -> AOV 1600.00, 64.0%
    # EMEA: ORD-2 ($1000) = $1000, 1 order -> AOV 1000.00, 20.0%
    # APAC: ORD-3 ($800) = $800, 1 order -> AOV 800.00, 16.0%
    assert len(regional) == 3
    na = regional[0]
    assert na["region"] == "North America"
    assert na["revenue"] == 3200.00
    assert na["order_count"] == 2
    assert na["aov"] == 1600.00
    assert na["share_of_total_pct"] == 64.00

    emea = regional[1]
    assert emea["region"] == "EMEA"
    assert emea["revenue"] == 1000.00
    assert emea["order_count"] == 1
    assert emea["aov"] == 1000.00
    assert emea["share_of_total_pct"] == 20.00


def test_top_concentration(synthetic_test_df):
    """Verify top concentration share percentage."""
    # Top 1 is P-1 ($2800 / $5000 = 56.0%)
    # Top 2 is P-1 + P-2 ($4200 / $5000 = 84.0%)
    conc_top1 = compute_top_concentration(synthetic_test_df, top_n=1)
    conc_top2 = compute_top_concentration(synthetic_test_df, top_n=2)
    assert conc_top1 == 56.00
    assert conc_top2 == 84.00


def test_data_profiler(synthetic_test_df):
    """Verify completeness score and schema validation."""
    profile = profile_dataset(synthetic_test_df)
    assert profile["completeness_score"] == 100.0
    assert profile["duplicate_rows"] == 0
    assert len(profile["columns_profile"]) == 12
    assert profile["validation_status"] == "valid"

    # Test with NaN introduced
    df_with_nan = synthetic_test_df.copy()
    df_with_nan.loc[0, "customer_segment"] = None
    profile_nan = profile_dataset(df_with_nan)
    # Total cells: 5 * 12 = 60, nulls: 1 -> 59/60 = 98.33%
    assert profile_nan["completeness_score"] == pytest.approx(98.33, rel=1e-2)


def test_insight_generator(synthetic_test_df):
    """Verify deterministic insight generation."""
    analytics = run_full_analytics(synthetic_test_df)
    insights = generate_automated_insights(
        metrics=analytics["metrics"],
        monthly_trends=analytics["monthly_trends"],
        top_products=analytics["top_products"],
        regional_performance=analytics["regional_performance"],
        top5_concentration_pct=analytics["top5_revenue_concentration_pct"],
    )
    assert len(insights) >= 3
    # Check that peak month insight exists
    insight_ids = [i["id"] for i in insights]
    assert "insight-peak-month" in insight_ids
    assert "insight-lead-product" in insight_ids
    assert "insight-regional-distribution" in insight_ids


def test_api_sample_endpoint():
    """Verify FastAPI /api/sample endpoint produces valid complete AnalysisResponse."""
    client = TestClient(app)
    
    # Ensure sample CSV exists before calling
    if not SAMPLE_CSV_PATH.exists():
        data = generate_b2b_sales_data(row_count=1500, seed=42)
        SAMPLE_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(SAMPLE_CSV_PATH, index=False)

    resp = client.post("/api/sample")
    assert resp.status_code == 200
    body = resp.json()

    assert body["dataset_meta"]["row_count"] == 1500
    assert body["dataset_meta"]["filename"] == "b2b_sales_sample.csv"
    assert body["metrics"]["total_revenue"] > 0
    assert body["metrics"]["total_orders"] > 0
    assert len(body["monthly_trends"]) == 12
    assert len(body["top_products"]) == 10
    assert len(body["regional_performance"]) == 4
    assert len(body["automated_insights"]) >= 3
    assert len(body["preview_rows"]) == 50


def test_api_upload_endpoint():
    """Verify FastAPI /api/upload with valid and invalid inputs."""
    client = TestClient(app)

    # 1. Valid CSV upload
    csv_bytes = b"order_id,order_date,customer_id,customer_segment,product_id,product_name,category,region,quantity,unit_price,discount,revenue\nORD-1,2024-01-01,C-1,Enterprise,P-1,Cloud Server,Cloud,North America,2,1000.0,0.0,2000.0\nORD-2,2024-01-02,C-2,Mid-Market,P-2,Firewall,Security,EMEA,1,500.0,0.0,500.0\nORD-3,2024-01-03,C-3,Enterprise,P-1,Cloud Server,Cloud,North America,1,1000.0,0.1,900.0\nORD-4,2024-01-04,C-4,SMB,P-3,Router,Network,APAC,3,300.0,0.0,900.0\nORD-5,2024-01-05,C-5,Enterprise,P-2,Firewall,Security,EMEA,2,500.0,0.0,1000.0\n"
    
    resp = client.post("/api/upload", files={"file": ("test_upload.csv", csv_bytes, "text/csv")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["dataset_meta"]["row_count"] == 5
    assert body["metrics"]["total_revenue"] == 5300.00
    assert body["metrics"]["total_orders"] == 5

    # 2. Reject non-CSV file
    resp_bad_ext = client.post("/api/upload", files={"file": ("data.txt", b"some text", "text/plain")})
    assert resp_bad_ext.status_code == 400
    assert "Unsupported file format" in resp_bad_ext.json()["detail"]

    # 3. Reject empty file
    resp_empty = client.post("/api/upload", files={"file": ("empty.csv", b"", "text/csv")})
    assert resp_empty.status_code == 400
    assert "empty" in resp_empty.json()["detail"]

    # 4. Reject file missing required analytical revenue columns
    bad_csv = b"col_a,col_b,col_c\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n13,14,15\n"
    resp_bad_cols = client.post("/api/upload", files={"file": ("bad_schema.csv", bad_csv, "text/csv")})
    assert resp_bad_cols.status_code == 400
    assert "missing required analytical revenue columns" in resp_bad_cols.json()["detail"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
