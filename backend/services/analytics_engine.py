"""
Deterministic analytical calculation engine.
All calculations are performed strictly via Pandas/NumPy.
"""

from typing import Dict, List, Any
import numpy as np
import pandas as pd


def compute_core_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate baseline executive KPIs: Revenue, Order Count, AOV, Units, Discount."""
    if df.empty:
        return {
            "total_revenue": 0.0,
            "total_orders": 0,
            "average_order_value": 0.0,
            "total_units_sold": 0,
            "average_discount": 0.0,
        }

    total_revenue = float(round(df["revenue"].sum(), 2))
    total_orders = int(df["order_id"].nunique()) if "order_id" in df.columns else int(len(df))
    average_order_value = float(round(total_revenue / total_orders, 2)) if total_orders > 0 else 0.0
    total_units_sold = int(df["quantity"].sum()) if "quantity" in df.columns else 0
    average_discount = float(round(df["discount"].mean(), 4)) if "discount" in df.columns else 0.0

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "average_order_value": average_order_value,
        "total_units_sold": total_units_sold,
        "average_discount": average_discount,
    }


def compute_monthly_trends(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate monthly revenue, order volume, and month-over-month growth rate."""
    if df.empty or "order_date" not in df.columns:
        return []

    df_copy = df.copy()
    df_copy["dt"] = pd.to_datetime(df_copy["order_date"], errors="coerce")
    df_copy = df_copy.dropna(subset=["dt"])

    if df_copy.empty:
        return []

    df_copy["month_str"] = df_copy["dt"].dt.strftime("%Y-%m")
    
    # Aggregation
    grouped = df_copy.groupby("month_str").agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique") if "order_id" in df_copy.columns else ("revenue", "count"),
    ).reset_index().sort_values("month_str")

    trends: List[Dict[str, Any]] = []
    prev_rev = None

    for _, row in grouped.iterrows():
        rev = float(round(row["revenue"], 2))
        orders = int(row["order_count"])
        
        mom_growth = None
        if prev_rev is not None and prev_rev > 0:
            mom_growth = float(round(((rev - prev_rev) / prev_rev) * 100.0, 2))
            
        trends.append({
            "month": str(row["month_str"]),
            "revenue": rev,
            "order_count": orders,
            "mom_growth_pct": mom_growth,
        })
        prev_rev = rev

    return trends


def compute_top_products(df: pd.DataFrame, limit: int = 10) -> List[Dict[str, Any]]:
    """Calculate top products ranked by revenue, including category, units sold, and revenue share."""
    if df.empty or "product_name" not in df.columns:
        return []

    total_revenue = float(df["revenue"].sum()) if df["revenue"].sum() > 0 else 1.0

    group_cols = ["product_name"]
    has_id = "product_id" in df.columns
    has_cat = "category" in df.columns

    agg_dict = {
        "revenue": "sum",
        "quantity": "sum" if "quantity" in df.columns else "count",
    }
    if has_id:
        agg_dict["product_id"] = "first"
    if has_cat:
        agg_dict["category"] = "first"

    grouped = df.groupby(group_cols).agg(agg_dict).reset_index()
    grouped = grouped.sort_values(by="revenue", ascending=False).head(limit)

    results: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        rev = float(round(row["revenue"], 2))
        share = float(round((rev / total_revenue) * 100.0, 2))
        units = int(row["quantity"])
        prod_id = str(row["product_id"]) if has_id else "N/A"
        cat = str(row["category"]) if has_cat else "General"

        results.append({
            "product_id": prod_id,
            "product_name": str(row["product_name"]),
            "category": cat,
            "revenue": rev,
            "units_sold": units,
            "share_of_total_pct": share,
        })

    return results


def compute_regional_performance(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Calculate regional performance breakdown: revenue, orders, AOV, and share."""
    if df.empty or "region" not in df.columns:
        return []

    total_revenue = float(df["revenue"].sum()) if df["revenue"].sum() > 0 else 1.0

    grouped = df.groupby("region").agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique") if "order_id" in df.columns else ("revenue", "count"),
    ).reset_index().sort_values(by="revenue", ascending=False)

    results: List[Dict[str, Any]] = []
    for _, row in grouped.iterrows():
        rev = float(round(row["revenue"], 2))
        orders = int(row["order_count"])
        aov = float(round(rev / orders, 2)) if orders > 0 else 0.0
        share = float(round((rev / total_revenue) * 100.0, 2))

        results.append({
            "region": str(row["region"]),
            "revenue": rev,
            "order_count": orders,
            "aov": aov,
            "share_of_total_pct": share,
        })

    return results


def compute_top_concentration(df: pd.DataFrame, top_n: int = 5) -> float:
    """Calculate the revenue share percentage of the top N products."""
    if df.empty or "revenue" not in df.columns:
        return 0.0

    total_revenue = float(df["revenue"].sum())
    if total_revenue <= 0:
        return 0.0

    prod_col = "product_id" if "product_id" in df.columns else "product_name"
    if prod_col not in df.columns:
        return 0.0

    top_revenue = df.groupby(prod_col)["revenue"].sum().nlargest(top_n).sum()
    return float(round((top_revenue / total_revenue) * 100.0, 2))


def run_full_analytics(df: pd.DataFrame) -> Dict[str, Any]:
    """Execute the complete analytical suite and return consolidated metrics dictionary."""
    metrics = compute_core_metrics(df)
    monthly_trends = compute_monthly_trends(df)
    top_products = compute_top_products(df, limit=10)
    regional = compute_regional_performance(df)
    concentration_pct = compute_top_concentration(df, top_n=5)

    return {
        "metrics": metrics,
        "monthly_trends": monthly_trends,
        "top_products": top_products,
        "regional_performance": regional,
        "top5_revenue_concentration_pct": concentration_pct,
    }
