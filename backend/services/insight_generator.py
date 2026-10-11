"""
Deterministic rule-based analytical insights generator.
Derives fact-checked, high-conviction narrative takeaways directly from computed aggregations.
"""

from typing import List, Dict, Any


def generate_automated_insights(
    metrics: Dict[str, Any],
    monthly_trends: List[Dict[str, Any]],
    top_products: List[Dict[str, Any]],
    regional_performance: List[Dict[str, Any]],
    top5_concentration_pct: float,
) -> List[Dict[str, Any]]:
    """Derive 3-6 grounded, deterministic analytical observations from verified metrics."""
    insights: List[Dict[str, Any]] = []

    # 1. Monthly Revenue Extremes
    if monthly_trends:
        sorted_by_rev = sorted(monthly_trends, key=lambda x: x["revenue"], reverse=True)
        peak_month = sorted_by_rev[0]
        trough_month = sorted_by_rev[-1]

        insights.append({
            "id": "insight-peak-month",
            "category": "performance",
            "title": f"Peak Revenue Month: {peak_month['month']}",
            "description": (
                f"Revenue peaked in {peak_month['month']} at ${peak_month['revenue']:,.2f} "
                f"across {peak_month['order_count']:,} orders. "
                f"The lowest volume period was {trough_month['month']} at ${trough_month['revenue']:,.2f}."
            ),
            "metric_reference": f"${peak_month['revenue']:,.2f}",
        })

        # 2. Month-over-Month Velocity Outliers
        valid_growth_months = [m for m in monthly_trends if m["mom_growth_pct"] is not None]
        if valid_growth_months:
            max_gain = max(valid_growth_months, key=lambda x: x["mom_growth_pct"])
            max_drop = min(valid_growth_months, key=lambda x: x["mom_growth_pct"])

            if max_gain["mom_growth_pct"] > 0:
                insights.append({
                    "id": "insight-mom-surge",
                    "category": "growth",
                    "title": f"Strongest Monthly Acceleration: {max_gain['month']}",
                    "description": (
                        f"{max_gain['month']} recorded the highest sequential expansion, "
                        f"growing +{max_gain['mom_growth_pct']:.1f}% month-over-month "
                        f"to reach ${max_gain['revenue']:,.2f}."
                    ),
                    "metric_reference": f"+{max_gain['mom_growth_pct']:.1f}%",
                })

            if max_drop["mom_growth_pct"] < 0:
                insights.append({
                    "id": "insight-mom-contraction",
                    "category": "growth",
                    "title": f"Largest Monthly Contraction: {max_drop['month']}",
                    "description": (
                        f"{max_drop['month']} experienced the sharpest decline, "
                        f"contracting {max_drop['mom_growth_pct']:.1f}% month-over-month."
                    ),
                    "metric_reference": f"{max_drop['mom_growth_pct']:.1f}%",
                })

    # 3. Product Driver & Catalog Concentration
    if top_products:
        lead_product = top_products[0]
        insights.append({
            "id": "insight-lead-product",
            "category": "concentration",
            "title": f"Primary Revenue Driver: {lead_product['product_name']}",
            "description": (
                f"'{lead_product['product_name']}' is the top-performing SKU, generating "
                f"${lead_product['revenue']:,.2f} ({lead_product['share_of_total_pct']:.1f}% of total sales) "
                f"with {lead_product['units_sold']:,} units sold."
            ),
            "metric_reference": f"{lead_product['share_of_total_pct']:.1f}% share",
        })

    if top5_concentration_pct > 0:
        concentration_desc = (
            f"The top 5 product SKUs account for {top5_concentration_pct:.1f}% of total gross revenue."
        )
        if top5_concentration_pct > 60.0:
            concentration_desc += " Indicates high portfolio concentration on a select group of flagship offerings."
        else:
            concentration_desc += " Reflects a well-diversified product portfolio."

        insights.append({
            "id": "insight-catalog-concentration",
            "category": "concentration",
            "title": "Top-5 Product Concentration",
            "description": concentration_desc,
            "metric_reference": f"{top5_concentration_pct:.1f}%",
        })

    # 4. Regional Distribution
    if regional_performance:
        top_region = regional_performance[0]
        bottom_region = regional_performance[-1]

        insights.append({
            "id": "insight-regional-distribution",
            "category": "outlier",
            "title": f"Leading Regional Market: {top_region['region']}",
            "description": (
                f"{top_region['region']} leads all territories with ${top_region['revenue']:,.2f} "
                f"({top_region['share_of_total_pct']:.1f}% of global volume, AOV ${top_region['aov']:,.2f}). "
                f"The smallest regional contribution is {bottom_region['region']} at ${bottom_region['revenue']:,.2f} "
                f"({bottom_region['share_of_total_pct']:.1f}%)."
            ),
            "metric_reference": f"{top_region['share_of_total_pct']:.1f}%",
        })

    return insights
