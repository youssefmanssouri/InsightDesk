"""
FastAPI application entrypoint for InsightDesk.
Exposes deterministic analytics API endpoints and grounded AI analyst capabilities.
"""

import io
import uuid
from typing import Dict, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from core.config import (
    SAMPLE_CSV_PATH,
    MAX_UPLOAD_SIZE_BYTES,
    REQUIRED_COLUMNS,
    MIN_ROWS_REQUIRED,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_QUESTION_LENGTH,
)
from models.schemas import (
    AnalysisResponse,
    DatasetMeta,
    DateRange,
    AskQuestionRequest,
    AskQuestionResponse,
    AiStatusResponse,
)
from services.analytics_engine import run_full_analytics
from services.data_profiler import profile_dataset
from services.insight_generator import generate_automated_insights
from services.ai_analyst import answer_analytical_question

app = FastAPI(
    title="InsightDesk Analytics API",
    description="Deterministic Python/Pandas analytical engine and grounded AI Analyst.",
    version="1.0.0",
)

# CORS configuration for client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active session and dataset cache (bounded in-memory)
MAX_CACHED_SESSIONS = 50
DATASET_SESSIONS: Dict[str, AnalysisResponse] = {}
ACTIVE_SESSION: dict = {
    "df": None,
    "dataset_id": None,
    "response": None,
}


def _cache_session(dataset_id: str, response: AnalysisResponse) -> None:
    """Bounded session caching to prevent unbounded memory growth."""
    if len(DATASET_SESSIONS) >= MAX_CACHED_SESSIONS:
        oldest_key = next(iter(DATASET_SESSIONS))
        DATASET_SESSIONS.pop(oldest_key, None)
    DATASET_SESSIONS[dataset_id] = response


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitizes numerical and categorical columns to prevent parsing anomalies
    from currency symbols, commas, percentages, and leading/trailing whitespace.
    """
    df = df.copy()

    def clean_num_series(series: pd.Series) -> pd.Series:
        if pd.api.types.is_numeric_dtype(series):
            return pd.to_numeric(series, errors="coerce")
        cleaned = (
            series.astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )
        return pd.to_numeric(cleaned, errors="coerce")

    # Clean numerical columns
    for col in ["revenue", "quantity", "unit_price", "discount"]:
        if col in df.columns:
            df[col] = clean_num_series(df[col])

    # If discount is in range 0-100 (e.g. 10 instead of 0.10), normalize
    if "discount" in df.columns:
        if (df["discount"] > 1.0).any():
            df["discount"] = df["discount"] / 100.0
        df["discount"] = df["discount"].clip(lower=0.0, upper=1.0).fillna(0.0)

    # Derive revenue if completely missing or partially null
    if "quantity" in df.columns and "unit_price" in df.columns:
        disc = df["discount"] if "discount" in df.columns else 0.0
        derived_rev = (df["quantity"] * df["unit_price"] * (1.0 - disc)).round(2)
        if "revenue" not in df.columns:
            df["revenue"] = derived_rev
        else:
            df["revenue"] = df["revenue"].fillna(derived_rev)

    if "revenue" in df.columns:
        df["revenue"] = df["revenue"].fillna(0.0)

    # Clean string columns
    str_cols = [
        "order_id",
        "customer_id",
        "customer_segment",
        "product_id",
        "product_name",
        "category",
        "region",
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def _process_dataframe(df: pd.DataFrame, filename: str) -> AnalysisResponse:
    """Helper to profile, calculate analytics, assign dataset_id, and format into AnalysisResponse."""
    df = sanitize_dataframe(df)
    dataset_id = f"ds-{uuid.uuid4().hex[:8]}"

    # Date range extraction
    date_range = None
    if "order_date" in df.columns:
        valid_dates = pd.to_datetime(df["order_date"], errors="coerce").dropna()
        if not valid_dates.empty:
            date_range = DateRange(
                start=valid_dates.min().strftime("%Y-%m-%d"),
                end=valid_dates.max().strftime("%Y-%m-%d"),
            )

    meta = DatasetMeta(
        filename=filename,
        row_count=len(df),
        column_count=len(df.columns),
        date_range=date_range,
    )

    data_quality = profile_dataset(df)
    analytics_payload = run_full_analytics(df)

    insights = generate_automated_insights(
        metrics=analytics_payload["metrics"],
        monthly_trends=analytics_payload["monthly_trends"],
        top_products=analytics_payload["top_products"],
        regional_performance=analytics_payload["regional_performance"],
        top5_concentration_pct=analytics_payload["top5_revenue_concentration_pct"],
    )

    # Preview rows (first 50 records)
    preview_df = df.head(50).copy()
    preview_rows = preview_df.fillna("").to_dict(orient="records")

    response = AnalysisResponse(
        dataset_id=dataset_id,
        dataset_meta=meta,
        data_quality=data_quality,
        metrics=analytics_payload["metrics"],
        monthly_trends=analytics_payload["monthly_trends"],
        top_products=analytics_payload["top_products"],
        regional_performance=analytics_payload["regional_performance"],
        top5_revenue_concentration_pct=analytics_payload["top5_revenue_concentration_pct"],
        automated_insights=insights,
        preview_rows=preview_rows,
    )

    # Store in memory session mapping
    _cache_session(dataset_id, response)
    ACTIVE_SESSION["df"] = df
    ACTIVE_SESSION["dataset_id"] = dataset_id
    ACTIVE_SESSION["response"] = response

    return response


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify API server readiness and AI configuration."""
    has_active_dataset = ACTIVE_SESSION["response"] is not None
    return {
        "status": "healthy",
        "service": "InsightDesk Analytics Engine",
        "has_active_dataset": has_active_dataset,
        "active_dataset_id": ACTIVE_SESSION.get("dataset_id"),
        "ai_configured": bool(GEMINI_API_KEY),
        "ai_model": GEMINI_MODEL,
    }


@app.get("/api/ai/status", response_model=AiStatusResponse, tags=["AI Analyst"])
def get_ai_status():
    """Check whether Gemini AI integration is configured and active."""
    return AiStatusResponse(
        configured=bool(GEMINI_API_KEY),
        model=GEMINI_MODEL,
    )


@app.post("/api/sample", response_model=AnalysisResponse, tags=["Analytics"])
def load_sample_dataset():
    """Load the bundled benchmark B2B sales dataset and return complete analysis."""
    if not SAMPLE_CSV_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark sample CSV not found at {SAMPLE_CSV_PATH}. Ensure data generator has run.",
        )

    try:
        df = pd.read_csv(SAMPLE_CSV_PATH)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read benchmark sample dataset: {str(exc)}",
        )

    return _process_dataframe(df, filename="b2b_sales_sample.csv")


@app.post("/api/upload", response_model=AnalysisResponse, tags=["Analytics"])
async def upload_csv(file: UploadFile = File(...)):
    """Accept and analyze a user-provided CSV dataset."""
    filename = file.filename or "uploaded_data.csv"

    # 1. File extension validation
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{filename}'. InsightDesk accepts standard CSV files only.",
        )

    # 2. File size and content reading
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file is empty (0 bytes).",
        )

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowable size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    # 3. Parse CSV with Pandas
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed CSV content. Parsing error: {str(exc)}",
        )

    # 4. Row count validation
    if len(df) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file contains headers but no data rows.",
        )

    if len(df) < MIN_ROWS_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The uploaded dataset contains only {len(df)} rows. A minimum of {MIN_ROWS_REQUIRED} rows is required for meaningful analytical breakdown.",
        )

    # 5. Core column requirements
    has_revenue = "revenue" in df.columns
    has_derived = "quantity" in df.columns and "unit_price" in df.columns
    if not has_revenue and not has_derived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Dataset is missing required analytical revenue columns. "
                "Expected either 'revenue' or both 'quantity' and 'unit_price'."
            ),
        )

    return _process_dataframe(df, filename=filename)


@app.post("/api/ask", response_model=AskQuestionResponse, tags=["AI Analyst"])
def ask_question(request: AskQuestionRequest):
    """
    Answer an analytical question grounded strictly in pre-computed metrics.
    Python calculates; AI explains.
    Enforces strict dataset isolation.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters.",
        )

    # Strict dataset session resolution
    target_analysis: Optional[AnalysisResponse] = None
    if request.dataset_id:
        target_analysis = DATASET_SESSIONS.get(request.dataset_id)
        if not target_analysis:
            # Reject unknown or expired dataset ID to prevent cross-dataset contamination
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset session '{request.dataset_id}' not found or has expired. Please reload or re-upload your dataset.",
            )
    else:
        # If no dataset_id specified, fallback to currently active session
        target_analysis = ACTIVE_SESSION.get("response")

    if not target_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active dataset available to query. Please load the sample dataset or upload a CSV first.",
        )

    return answer_analytical_question(question, target_analysis)
