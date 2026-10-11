# InsightDesk

InsightDesk is a business sales analytics application designed to deliver deterministic, fact-grounded reporting from transactional datasets. 

The application architecture enforces strict separation of concerns:
- **Computation**: Pure Python and Pandas calculate 100% of arithmetic, metric aggregations, and data profiling.
- **Presentation**: A clean, modular React frontend visualizes verified data contracts using Recharts and tabular formatting.
- **AI Explanation**: An AI analyst grounded strictly in verified calculation summaries explains the data in natural language without computing numbers or fabricating claims.

**Core Principle: Python calculates; AI explains.**

---

## Status: Phase 4 Complete (100%)

All 4 phases are fully implemented, audited, hardened, and verified with 28 automated tests.

- **Phase 1: Backend Analytics Foundation (25%)** — Completed
- **Phase 2: Frontend Dashboard Shell & Visual Analytics (25%)** — Completed
- **Phase 3: Grounded AI Analyst Layer (25%)** — Completed
- **Phase 4: Final Audit, Hardening & Verification (25%)** — Completed
- **Total Progress: 100%**

---

## Architecture & Product Principles

1. **Deterministic Calculations First**: All aggregations (revenue, order counts, average order value, units sold, monthly growth, regional distribution, top product rankings, concentration indices) are calculated by Pandas in `analytics_engine.py`.
2. **Strict Dataset Isolation**: Each dataset load/upload generates a unique `dataset_id`. Requests to `/api/ask` must match an active session; requests with unknown or expired dataset IDs immediately return `404 Not Found` rather than silently leaking data from other sessions.
3. **Session Cache Management**: In-memory sessions are managed with a bounded Least-Recently-Used (LRU) cache (capacity: 50 sessions) to avoid unbounded memory growth.
4. **Input Sanitization & Data Hardening**:
   - Currency strings with symbols (`$`, `€`, `£`, commas, whitespace) in numeric fields are cleaned and normalized.
   - When gross revenue is omitted or null, it is deterministically derived from `quantity * unit_price * (1 - discount)`.
   - Percentage discounts provided as whole numbers (e.g., `10` for 10%) are safely normalized to fractions (`0.10`).
   - Negative values (such as returns, credit adjustments, or refunds) are faithfully preserved without silent alteration and transparently surfaced by the Data Quality Profiler.
   - Columns in arbitrary order or with unexpected extra attributes are parsed seamlessly.
5. **Grounded AI Analyst**:
   - **Zero Raw Data Exposure**: Gemini is never sent raw CSV rows; it receives pre-computed analytical summaries.
   - **Fact Verification**: Observed facts returned by the AI are deterministically validated and cross-referenced with backend values.
   - **Credential Protection**: API errors and exception traces strictly redact all API keys and credential strings before reaching clients.
   - **Active Model Verification**: Primary model defaults to `gemini-2.5-flash` with fallback to `gemini-3.8-flash`. Deprecated models (such as 1.5/2.0) are completely excluded.
   - **Refusal of Out-of-Scope Questions**: The AI refuses to answer questions regarding metrics absent from the dataset (e.g., competitor data, marketing spend).
6. **Synthetic Sample Data**: The benchmark dataset (`b2b_sales_sample.csv`, 1,500 rows, 1,144 unique orders, generated with seed 42) is synthetic sample data created specifically for deterministic validation and demonstration.

---

## Setup & Running InsightDesk

### Prerequisites
- Node.js (v18+) and npm
- Python (v3.10+)

### 1. Environment Configuration
Copy `.env.example` to `.env` or set environment variables in your terminal:

```powershell
# Optional: Set your Gemini API key from Google AI Studio (https://aistudio.google.com/)
$env:GEMINI_API_KEY="your_api_key_here"

# Optional: configure model (default: gemini-2.5-flash)
$env:GEMINI_MODEL="gemini-2.5-flash"
```

*Note: If no API key is provided, the application and dashboard remain 100% functional, and the AI panel gracefully indicates that the AI analyst is unconfigured.*

### 2. Backend Startup
From the project root:

```powershell
# Activate Python virtual environment
.\backend\.venv\Scripts\Activate.ps1

# Install dependencies (if not already installed)
pip install -r backend\requirements.txt

# Start the FastAPI server
.\backend\.venv\Scripts\uvicorn main:app --app-dir backend --port 8000
```

The backend API will run on `http://127.0.0.1:8000`.

### 3. Frontend Startup
In a separate terminal:

```powershell
cd frontend

# Install dependencies (if not already installed)
npm install --legacy-peer-deps

# Start the Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```

Open your browser to `http://127.0.0.1:5173/`.

### 4. Production Build Verification
To verify the frontend TypeScript types and production bundle:

```powershell
cd frontend
npm run build
```

---

## API Endpoints

| Method | Endpoint | Description | Request Payload | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Server and AI readiness check | None | JSON |
| `GET` | `/api/ai/status` | Gemini configuration status | None | `AiStatusResponse` |
| `POST` | `/api/sample` | Load & analyze benchmark dataset | None | `AnalysisResponse` |
| `POST` | `/api/upload` | Upload & analyze custom CSV | `multipart/form-data` | `AnalysisResponse` |
| `POST` | `/api/ask` | Grounded analytical question answering | `{"question": "...", "dataset_id": "..."}` | `AskQuestionResponse` |

---

## Test Verification Suite

The backend test suite includes 28 automated tests across calculation accuracy, data profiling, endpoint routing, data hardening, session isolation, and AI grounding:

```powershell
.\backend\.venv\Scripts\pytest backend\tests -v
```

### Test Suite Structure (28 passing tests):
1. **`test_analytics_verification.py` (9 tests)**:
   - Core metrics ground-truth arithmetic (revenue, order counts, AOV, units sold).
   - Monthly trend calculation and MoM revenue growth.
   - Top products revenue ranking and revenue share percentages.
   - Regional performance revenue and order share.
   - Top product concentration index.
   - Data profiler completeness, row counts, and missing value checks.
   - Automated business insight generator.
   - `/api/sample` endpoint contract verification.
   - `/api/upload` endpoint validation with valid CSV.
2. **`test_dataset_isolation.py` (4 tests)**:
   - Sequential dataset loading yields distinct unique identifiers.
   - Question answering respects specific `dataset_id` context.
   - Submitting an unknown or expired `dataset_id` returns HTTP 404.
   - Omitted `dataset_id` safely defaults to currently active session.
3. **`test_data_hardening.py` (5 tests)**:
   - Sanitization of currency symbols (`$`, `,`, whitespace) in numeric fields.
   - Derivation of revenue when omitted or null (`quantity * unit_price * (1 - discount)`).
   - Clipping of negative non-refundable values.
   - Resilience against unusual column orders and extra unexpected columns.
   - LRU cache bounded capacity enforcement (evicts oldest session when limit is reached).
4. **`test_ai_analyst.py` (10 tests)**:
   - Grounded context contains only pre-computed summaries, never raw CSV lines.
   - Missing API key graceful fallback.
   - Empty question and excessive question length validation (HTTP 422 / handled).
   - Successful mocked Gemini response parsing into structured facts and recommendations.
   - Rejection of unanswerable or out-of-scope questions.
   - Timeout and provider failure handling.
   - `/api/ask` endpoint without active dataset handling.
   - `/api/ask` endpoint with active dataset integration.
   - `/api/ai/status` endpoint validation.

---

## Known Architecture Limitations

1. **In-Memory Storage**: Dataset sessions are stored in an in-memory LRU cache on the backend process. If the backend process restarts, previously uploaded sessions are cleared and datasets must be reloaded. (For local single-user analysis, this avoids unnecessary external database infrastructure).
2. **Schema Assumptions**: The CSV ingestion pipeline expects business sales transactions containing order identifiers, dates, products, regions, quantities, and unit prices. General non-sales tabular datasets (e.g., biological or HR datasets) will be rejected with an informative schema error.
3. **Single Active Node**: The current architecture is designed for single-node local execution without distributed worker synchronization.
