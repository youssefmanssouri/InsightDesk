"""
Live HTTP end-to-end integration test against running uvicorn server.
"""

import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_CSV_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "b2b_sales_sample.csv"

def run_live_tests():
    print(f"Connecting to live server at {BASE_URL}...")
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Test /health
        r_health = client.get("/health")
        print(f"GET /health: {r_health.status_code}")
        assert r_health.status_code == 200, f"Expected 200, got {r_health.status_code}"
        health_data = r_health.json()
        print(f"Health response: {health_data}")
        assert health_data["status"] == "healthy"

        # 2. Test /api/sample
        r_sample = client.post("/api/sample")
        print(f"POST /api/sample: {r_sample.status_code}")
        assert r_sample.status_code == 200, f"Expected 200, got {r_sample.status_code}"
        sample_data = r_sample.json()
        meta = sample_data["dataset_meta"]
        metrics = sample_data["metrics"]
        print(f"Sample loaded: {meta['row_count']} rows, revenue: ${metrics['total_revenue']:,.2f}, orders: {metrics['total_orders']}")
        assert meta["row_count"] == 1500
        assert metrics["total_revenue"] > 0
        assert len(sample_data["monthly_trends"]) == 12
        assert len(sample_data["top_products"]) == 10
        assert len(sample_data["regional_performance"]) == 4

        # 3. Test /api/upload with b2b_sales_sample.csv
        print(f"Uploading file {SAMPLE_CSV_PATH} to POST /api/upload...")
        with open(SAMPLE_CSV_PATH, "rb") as f:
            files = {"file": ("uploaded_b2b_sales.csv", f, "text/csv")}
            r_upload = client.post("/api/upload", files=files)
        print(f"POST /api/upload: {r_upload.status_code}")
        assert r_upload.status_code == 200, f"Expected 200, got {r_upload.status_code}"
        upload_data = r_upload.json()
        assert upload_data["dataset_meta"]["filename"] == "uploaded_b2b_sales.csv"
        assert upload_data["dataset_meta"]["row_count"] == 1500
        assert upload_data["metrics"]["total_revenue"] == metrics["total_revenue"]
        print(f"Upload successfully processed and verified! Revenue: ${upload_data['metrics']['total_revenue']:,.2f}")

        # 4. Test upload validation: reject non-csv
        r_bad_ext = client.post("/api/upload", files={"file": ("invalid.txt", b"hello world", "text/plain")})
        print(f"POST /api/upload invalid extension: {r_bad_ext.status_code}")
        assert r_bad_ext.status_code == 400

        # 5. Test upload validation: reject empty file
        r_empty = client.post("/api/upload", files={"file": ("empty.csv", b"", "text/csv")})
        print(f"POST /api/upload empty file: {r_empty.status_code}")
        assert r_empty.status_code == 400

        print("\nALL LIVE HTTP TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_live_tests()
