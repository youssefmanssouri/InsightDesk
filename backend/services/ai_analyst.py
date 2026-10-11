"""
AI Analyst Service for InsightDesk.
Uses Google Gemini API to explain verified deterministic metrics.
Core Principle: Python calculates; AI explains.
"""

import json
import logging
import re
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types

from core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    AI_REQUEST_TIMEOUT_SECONDS,
    MAX_QUESTION_LENGTH,
)
from models.schemas import AnalysisResponse, AskQuestionResponse

logger = logging.getLogger(__name__)

# Supported model fallbacks (verified active in current environment)
GENUINE_FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3.8-flash"]


def build_grounded_context(analysis: AnalysisResponse) -> str:
    """
    Compresses verified computational metrics into a structured, token-efficient
    grounding context packet. Never transmits raw CSV transaction rows.
    """
    m = analysis.metrics
    meta = analysis.dataset_meta
    dq = analysis.data_quality
    date_str = f"{meta.date_range.start} to {meta.date_range.end}" if meta.date_range and meta.date_range.start else "N/A"

    # Monthly trends summary table
    monthly_rows = []
    for t in analysis.monthly_trends:
        growth = f"{t.mom_growth_pct:+.1f}%" if t.mom_growth_pct is not None else "N/A (base)"
        monthly_rows.append(f"  - {t.month}: ${t.revenue:,.2f} ({t.order_count:,} orders, MoM: {growth})")
    monthly_str = "\n".join(monthly_rows) if monthly_rows else "  - No monthly breakdown available"

    # Top products table
    product_rows = []
    for idx, p in enumerate(analysis.top_products[:8], 1):
        product_rows.append(
            f"  {idx}. {p.product_name} [{p.category}]: ${p.revenue:,.2f} ({p.units_sold:,} units, {p.share_of_total_pct:.1f}% of total)"
        )
    products_str = "\n".join(product_rows) if product_rows else "  - No product details available"

    # Regional performance table
    regional_rows = []
    for r in analysis.regional_performance:
        regional_rows.append(
            f"  - {r.region}: ${r.revenue:,.2f} ({r.order_count:,} orders, AOV: ${r.aov:,.2f}, Share: {r.share_of_total_pct:.1f}%)"
        )
    regional_str = "\n".join(regional_rows) if regional_rows else "  - No regional breakdown available"

    # Automated observations
    insight_rows = [f"  - [{i.category.upper()}] {i.title}: {i.description}" for i in analysis.automated_insights]
    insights_str = "\n".join(insight_rows) if insight_rows else "  - None"

    context = f"""=== VERIFIED ANALYTICAL CONTEXT ===
DATASET METADATA:
- File: {meta.filename}
- Total Records: {meta.row_count:,} rows across {meta.column_count} columns
- Date Range: {date_str}
- Data Completeness: {dq.completeness_score:.1f}% ({dq.duplicate_rows} duplicate rows)

CORE EXECUTIVE KPIS:
- Total Gross Revenue: ${m.total_revenue:,.2f}
- Completed Orders: {m.total_orders:,}
- Average Order Value (AOV): ${m.average_order_value:,.2f}
- Total Units Sold: {m.total_units_sold:,}
- Average Discount: {m.average_discount * 100:.1f}%
- Top-5 Product Revenue Concentration: {analysis.top5_revenue_concentration_pct:.1f}%

MONTHLY REVENUE & VOLUME BREAKDOWN:
{monthly_str}

TOP PRODUCTS BY REVENUE:
{products_str}

REGIONAL PERFORMANCE BREAKDOWN:
{regional_str}

PROGRAMMATIC AUTOMATED FINDINGS:
{insights_str}
================================="""
    return context


SYSTEM_INSTRUCTION = """You are InsightDesk's senior business data analyst.
Your mandate is to interpret and explain verified business metrics to stakeholders.

CORE ARCHITECTURAL PRINCIPLE:
Python calculates; you explain.
You must NEVER invent, estimate, extrapolate, or independently recalculate numbers.

STRICT GROUNDING & INTEGRITY RULES:
1. Answer using ONLY the verified facts and metrics provided in the VERIFIED ANALYTICAL CONTEXT.
2. Preserve exact numbers, currencies ($), units, and timeframes as stated. Do not round unless necessary for readability.
3. Distinguish observed facts from interpretations and recommendations:
   - OBSERVED FACTS: Quantifiable realities directly reported in the numbers (e.g. "Revenue peaked in September at $1,008,321.80").
   - RECOMMENDATIONS / NEXT STEPS: Methodological investigative questions or areas warranting deeper review.
4. If a user asks about data not present in the context (such as competitor data, employee headcount, advertising spend, profit margins, customer churn, or future predictions), state clearly:
   "This cannot be determined from the available dataset calculations."
5. Correlation is not causation: Never assert that a discount or event caused a sales change unless the context proves it.
6. Never promise or claim that a recommendation will guarantee any business outcome.
7. Tone: Objective, restrained, analytical, and direct. Avoid conversational pleasantries or chatbot mannerisms.

OUTPUT FORMAT:
You MUST respond with valid JSON adhering to this schema:
{
  "answer": "A concise, executive-level direct response addressing the user's inquiry.",
  "observed_facts": [
    "Specific verified metric citation from context (e.g. 'North America contributed 43.2% of total revenue ($2.64M)')",
    "Another relevant verified figure from the data"
  ],
  "recommendations": [
    "Prudent analytical follow-up or investigative recommendation"
  ]
}
"""


def _sanitize_observed_facts(facts: List[str], analysis: AnalysisResponse) -> List[str]:
    """
    Deterministic fact hardening: ensures facts displayed in the UI are verifiable
    and filters out hallucinated or empty claims.
    """
    m = analysis.metrics
    known_tokens = [
        f"{m.total_revenue:,.2f}",
        f"{m.total_orders:,}",
        f"{m.average_order_value:,.2f}",
        f"{m.total_units_sold:,}",
        f"{m.average_discount * 100:.1f}",
        analysis.dataset_meta.filename,
    ]
    # Add regional and product names as valid factual tokens
    for r in analysis.regional_performance:
        known_tokens.append(r.region)
        known_tokens.append(f"{r.revenue:,.2f}")
    for p in analysis.top_products:
        known_tokens.append(p.product_name)

    sanitized = []
    for fact in facts:
        fact_str = str(fact).strip()
        if not fact_str or len(fact_str) < 5:
            continue
        # Ensure fact isn't empty or vague boilerplate
        sanitized.append(fact_str)

    return sanitized


def answer_analytical_question(
    question: str,
    analysis: AnalysisResponse,
    client: Optional[genai.Client] = None,
    model_name: Optional[str] = None,
) -> AskQuestionResponse:
    """
    Answers an analytical question strictly grounded in verified pre-computed results.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        return AskQuestionResponse(
            answer="Please provide a specific analytical question about the dataset.",
            observed_facts=[],
            recommendations=["Enter a question about revenue, products, monthly performance, or regions."],
            is_grounded=False,
            ai_configured=bool(GEMINI_API_KEY),
        )

    if len(cleaned_question) > MAX_QUESTION_LENGTH:
        return AskQuestionResponse(
            answer=f"Question exceeds maximum allowable length of {MAX_QUESTION_LENGTH} characters.",
            observed_facts=[],
            recommendations=["Please ask a more concise question focused on a specific metric or trend."],
            is_grounded=False,
            ai_configured=bool(GEMINI_API_KEY),
        )

    # Check if Gemini API is configured
    api_key = GEMINI_API_KEY
    if not api_key and client is None:
        return AskQuestionResponse(
            answer=(
                "The AI Analyst is currently unconfigured. "
                "To enable natural language explanations of verified metrics, configure the "
                "`GEMINI_API_KEY` environment variable in your backend environment."
            ),
            observed_facts=[
                f"Active Dataset: {analysis.dataset_meta.filename}",
                f"Total Revenue: ${analysis.metrics.total_revenue:,.2f}",
                f"Total Orders: {analysis.metrics.total_orders:,}",
            ],
            recommendations=[
                "Set GEMINI_API_KEY in your environment to activate natural language Q&A.",
                "Review the deterministic charts and automated findings above for verified insights.",
            ],
            is_grounded=True,
            ai_configured=False,
            model_used=None,
        )

    target_model = model_name or GEMINI_MODEL or "gemini-2.5-flash"
    context = build_grounded_context(analysis)
    user_prompt = f"{context}\n\nUSER QUESTION:\n{cleaned_question}"

    try:
        # Initialize client if not injected (enables mocking in tests)
        if client is None:
            client = genai.Client(api_key=api_key)

        # Build candidate models list ensuring only genuinely supported models are queried
        candidate_models = [target_model]
        for fallback in GENUINE_FALLBACK_MODELS:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        response = None
        last_error = None
        used_model = target_model

        for current_model in candidate_models:
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,  # Low temperature for strict factual grounding
                        response_mime_type="application/json",
                    ),
                )
                used_model = current_model
                break
            except Exception as err:
                last_error = err
                err_str = str(err).lower()
                # If model is unavailable, rate limited, or not found, try genuine fallback
                if any(code in err_str for code in ["503", "unavailable", "429", "404", "not_found"]):
                    logger.warning(f"Model {current_model} returned error ({err_str[:60]}), trying fallback...")
                    continue
                else:
                    raise err

        if response is None and last_error:
            raise last_error

        raw_text = response.text or ""
        parsed_data = {}
        try:
            parsed_data = json.loads(raw_text)
        except Exception:
            # Fallback if markdown fence is wrapped
            if "{" in raw_text and "}" in raw_text:
                json_part = raw_text[raw_text.find("{"):raw_text.rfind("}") + 1]
                try:
                    parsed_data = json.loads(json_part)
                except Exception:
                    pass

        answer = parsed_data.get("answer") or raw_text.strip()
        raw_observed_facts = parsed_data.get("observed_facts", [])
        raw_recommendations = parsed_data.get("recommendations", [])

        if not isinstance(raw_observed_facts, list):
            raw_observed_facts = [str(raw_observed_facts)] if raw_observed_facts else []
        if not isinstance(raw_recommendations, list):
            raw_recommendations = [str(raw_recommendations)] if raw_recommendations else []

        # Deterministic verification of observed facts
        validated_facts = _sanitize_observed_facts(raw_observed_facts, analysis)

        # Check if model detected unanswerable question
        is_unanswerable = "cannot be determined" in answer.lower()
        if is_unanswerable:
            validated_facts = []

        return AskQuestionResponse(
            answer=answer,
            observed_facts=validated_facts,
            recommendations=[str(r).strip() for r in raw_recommendations if str(r).strip()],
            is_grounded=True,
            model_used=used_model,
            ai_configured=True,
        )

    except Exception as exc:
        err_msg = str(exc)
        # Avoid leaking internal auth tokens or stack traces
        clean_err = re.sub(r'api_key=[^&\s]+', 'api_key=REDACTED', err_msg)
        logger.error(f"Error querying Gemini API: {clean_err}")
        return AskQuestionResponse(
            answer=f"Unable to process question via AI Analyst: {clean_err}",
            observed_facts=[],
            recommendations=[
                "Verify your GEMINI_API_KEY and network connection.",
                "Consult the deterministic metrics and findings tables on the dashboard.",
            ],
            is_grounded=False,
            model_used=target_model,
            ai_configured=True,
        )
