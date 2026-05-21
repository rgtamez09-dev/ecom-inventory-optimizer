import pandas as pd
import numpy as np
from datetime import datetime, timedelta

SKUS = {
    'FC-001': {'name': 'Resistance Bands Set',  'price': 24.99, 'cogs': 8.50,  'lead_time': 35},
    'FC-002': {'name': 'Yoga Mat Pro',           'price': 39.99, 'cogs': 12.00, 'lead_time': 40},
    'FC-003': {'name': 'Foam Roller',            'price': 29.99, 'cogs': 9.50,  'lead_time': 35},
    'FC-004': {'name': 'Jump Rope Speed',        'price': 14.99, 'cogs': 4.00,  'lead_time': 30},
    'FC-005': {'name': 'Gym Gloves',             'price': 19.99, 'cogs': 6.50,  'lead_time': 30},
    'FC-006': {'name': 'Knee Sleeves (pair)',    'price': 34.99, 'cogs': 11.00, 'lead_time': 40},
    'FC-007': {'name': 'Shaker Bottle 700ml',   'price': 12.99, 'cogs': 3.50,  'lead_time': 25},
    'FC-008': {'name': 'Lifting Belt',           'price': 49.99, 'cogs': 16.00, 'lead_time': 45},
}

BASELINE_DEMAND = {
    'FC-001': 15, 'FC-002': 10, 'FC-003': 8,  'FC-004': 20,
    'FC-005': 12, 'FC-006': 6,  'FC-007': 25, 'FC-008': 4,
}

# Current stock mix: OK / EXCESS / CRITICAL / REORDER / STRANDED
CURRENT_STOCK = {
    'FC-001': 450,   # OK
    'FC-002': 1200,  # EXCESS (>90 days)
    'FC-003': 120,   # OK
    'FC-004': 18,    # CRITICAL (below safety stock)
    'FC-005': 500,   # EXCESS
    'FC-006': 90,    # OK, near reorder point
    'FC-007': 200,   # STRANDED (listing down)
    'FC-008': 20,    # REORDER NOW
}

STRANDED = {'FC-007'}


def generate_data(seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (sku_df, demand_df) with 90 days of simulated demand history."""
    np.random.seed(seed)

    today = datetime.today().date()
    date_range = [today - timedelta(days=90 - i) for i in range(90)]

    demand_records = []
    for sku, base in BASELINE_DEMAND.items():
        for date in date_range:
            month = date.month
            if month == 1:
                factor = 1.6    # New Year fitness peak
            elif month in [3, 4]:
                factor = 1.3    # Spring outdoor season
            else:
                factor = 1.0
            units = int(np.random.poisson(base * factor))
            demand_records.append({'date': date, 'sku': sku, 'units_sold': units})

    demand_df = pd.DataFrame(demand_records)

    sku_records = []
    for sku, info in SKUS.items():
        sku_records.append({
            'sku': sku,
            'product_name': info['name'],
            'price': info['price'],
            'cogs': info['cogs'],
            'lead_time_days': info['lead_time'],
            'current_stock': CURRENT_STOCK[sku],
            'is_stranded': sku in STRANDED,
        })

    sku_df = pd.DataFrame(sku_records)
    return sku_df, demand_df


if __name__ == '__main__':
    sku_df, demand_df = generate_data()
    print("SKU Master:")
    print(sku_df.to_string(index=False))
    print(f"\nDemand records: {len(demand_df)} rows ({demand_df['sku'].nunique()} SKUs × 90 days)")
