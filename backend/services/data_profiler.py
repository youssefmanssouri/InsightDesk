"""
Data profiling and schema quality evaluation service.
Computes dataset completeness, duplicate rows, and per-column health metrics.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
from core.config import REQUIRED_COLUMNS, MIN_ROWS_REQUIRED


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate thorough data health profile and column-level quality statistics."""
    row_count = int(len(df))
    column_count = int(len(df.columns))

    if row_count == 0 or column_count == 0:
        return {
            "completeness_score": 0.0,
            "duplicate_rows": 0,
            "columns_profile": [],
            "validation_status": "warning",
            "validation_notes": ["Dataset is empty."],
        }

    total_cells = row_count * column_count
    total_nulls = int(df.isna().sum().sum())
    completeness_score = float(round(((total_cells - total_nulls) / total_cells) * 100.0, 2))

    duplicate_rows = int(df.duplicated().sum())

    columns_profile: List[Dict[str, Any]] = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = float(round((null_count / row_count) * 100.0, 2))
        
        # Inferred type description
        dtype_str = str(df[col].dtype)
        if "datetime" in dtype_str or (dtype_str == "object" and "date" in col.lower()):
            inferred_type = "date/datetime"
        elif "int" in dtype_str:
            inferred_type = "integer"
        elif "float" in dtype_str:
            inferred_type = "float"
        elif "bool" in dtype_str:
            inferred_type = "boolean"
        else:
            inferred_type = "string/categorical"

        columns_profile.append({
            "name": str(col),
            "inferred_type": inferred_type,
            "null_count": null_count,
            "null_percentage": null_pct,
        })

    # Validate against expected core analytics columns
    validation_status, validation_notes = validate_dataset_schema(df)

    return {
        "completeness_score": completeness_score,
        "duplicate_rows": duplicate_rows,
        "columns_profile": columns_profile,
        "validation_status": validation_status,
        "validation_notes": validation_notes,
    }


def validate_dataset_schema(df: pd.DataFrame) -> Tuple[str, List[str]]:
    """Validate whether the dataframe has usable rows and minimum required analytical columns."""
    notes: List[str] = []
    status = "valid"

    if len(df) < MIN_ROWS_REQUIRED:
        status = "warning"
        notes.append(f"Dataset has only {len(df)} rows (minimum recommended: {MIN_ROWS_REQUIRED}).")

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        status = "warning"
        notes.append(f"Missing recommended analytical columns: {', '.join(missing_cols)}")

    # Check for revenue/quantity calculation validity if both present
    if "revenue" in df.columns and "quantity" in df.columns and "unit_price" in df.columns:
        if (df["revenue"] < 0).any():
            status = "warning"
            notes.append("Dataset contains negative revenue values.")

    return status, notes
