import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
SAMPLE_CSV_PATH = SAMPLE_DATA_DIR / "b2b_sales_sample.csv"

# Ingestion constraints
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit
MIN_ROWS_REQUIRED = 5

# Canonical analytics columns required for core reporting
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "customer_segment",
    "product_id",
    "product_name",
    "category",
    "region",
    "quantity",
    "unit_price",
    "discount",
    "revenue",
]

# AI Analyst Configuration (Gemini API)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
AI_REQUEST_TIMEOUT_SECONDS = 20
MAX_QUESTION_LENGTH = 500
