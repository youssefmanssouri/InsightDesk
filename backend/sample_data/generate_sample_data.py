"""
Deterministic generator for realistic B2B sales transactional dataset.
Schema:
order_id, order_date, customer_id, customer_segment, product_id,
product_name, category, region, quantity, unit_price, discount, revenue
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

PRODUCTS = [
    # (product_id, product_name, category, base_price, typical_qty_range)
    ("PRD-101", "Apex Cloud Server Cluster", "Cloud Infrastructure", 1250.00, (1, 8)),
    ("PRD-102", "Datamesh Object Storage 50TB", "Cloud Infrastructure", 240.00, (2, 20)),
    ("PRD-103", "Vanguard Managed Kubernetes Node", "Cloud Infrastructure", 420.00, (2, 15)),
    ("PRD-201", "Sentrix Endpoint Security Suite", "Enterprise Security", 850.00, (1, 10)),
    ("PRD-202", "ZeroTrust Perimeter Gateway", "Enterprise Security", 1400.00, (1, 5)),
    ("PRD-203", "ShieldLayer Threat Intelligence Feed", "Enterprise Security", 650.00, (1, 12)),
    ("PRD-301", "InsightPulse Real-Time Telemetry", "Analytics & Data", 950.00, (1, 6)),
    ("PRD-302", "VectorDB Neural Search Engine", "Analytics & Data", 1800.00, (1, 4)),
    ("PRD-303", "StreamPipe Kafka ETL Connector", "Analytics & Data", 320.00, (2, 16)),
    ("PRD-401", "CodeForge Enterprise CI/CD Runner", "Developer Tooling", 240.00, (2, 25)),
    ("PRD-402", "ArtifactVault Private Registry", "Developer Tooling", 580.00, (1, 8)),
    ("PRD-403", "DevWorkspace Cloud IDE Seat", "Developer Tooling", 120.00, (5, 40)),
]

REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
REGION_WEIGHTS = [0.45, 0.30, 0.18, 0.07]

SEGMENTS = ["Enterprise", "Mid-Market", "Small Business"]
SEGMENT_WEIGHTS = [0.40, 0.40, 0.20]

DISCOUNTS = [0.0, 0.05, 0.10, 0.15, 0.20]
DISCOUNT_WEIGHTS = [0.50, 0.25, 0.15, 0.07, 0.03]


def generate_b2b_sales_data(row_count: int = 1500, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_delta = (end_date - start_date).days

    # Customer base
    customers = [f"CUST-{1000 + i}" for i in range(120)]
    customer_segment_map = {
        cid: random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        for cid in customers
    }
    customer_region_map = {
        cid: random.choices(REGIONS, weights=REGION_WEIGHTS)[0]
        for cid in customers
    }

    rows = []
    current_order_num = 10001
    
    # Generate grouped by orders (approx 1.25 items per order)
    while len(rows) < row_count:
        order_id = f"ORD-2024-{current_order_num}"
        current_order_num += 1

        cid = random.choice(customers)
        segment = customer_segment_map[cid]
        region = customer_region_map[cid]
        
        # Seasonality: higher volume towards Q3/Q4
        day_offset = int(random.triangular(0, date_delta, date_delta * 0.75))
        order_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        
        # Multi-item orders
        items_in_order = random.choices([1, 2, 3], weights=[0.75, 0.20, 0.05])[0]
        chosen_products = random.sample(PRODUCTS, k=items_in_order)
        
        for prod in chosen_products:
            if len(rows) >= row_count:
                break
                
            prod_id, prod_name, category, base_price, qty_range = prod
            
            # Enterprise buyers purchase higher volume
            qty_mult = 1.5 if segment == "Enterprise" else 1.0
            quantity = max(1, int(random.randint(qty_range[0], qty_range[1]) * qty_mult))
            
            # Unit price has slight negotiated variance (+/- 4%)
            price_variance = random.uniform(0.96, 1.04)
            unit_price = round(base_price * price_variance, 2)
            
            discount = random.choices(DISCOUNTS, weights=DISCOUNT_WEIGHTS)[0]
            if segment == "Enterprise" and quantity > 10:
                discount = max(discount, 0.15)
                
            revenue = round(quantity * unit_price * (1.0 - discount), 2)
            
            rows.append({
                "order_id": order_id,
                "order_date": order_date,
                "customer_id": cid,
                "customer_segment": segment,
                "product_id": prod_id,
                "product_name": prod_name,
                "category": category,
                "region": region,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount": discount,
                "revenue": revenue,
            })
            
    df = pd.DataFrame(rows)
    # Sort chronologically
    df["order_date_dt"] = pd.to_datetime(df["order_date"])
    df = df.sort_values(by=["order_date_dt", "order_id"]).drop(columns=["order_date_dt"])
    return df


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent
    out_file = out_dir / "b2b_sales_sample.csv"
    data = generate_b2b_sales_data(row_count=1500, seed=42)
    data.to_csv(out_file, index=False)
    print(f"Generated {len(data)} rows to {out_file}")
