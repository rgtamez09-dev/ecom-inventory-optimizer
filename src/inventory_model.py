import pandas as pd
import numpy as np

SERVICE_LEVELS = {'95%': 1.65, '98%': 2.05, '99%': 2.58}

STATUS_COLOR = {
    'OK':          '#2ecc71',
    'REORDER NOW': '#f39c12',
    'CRITICAL':    '#e74c3c',
    'EXCESS':      '#9b59b6',
    'STOCKOUT':    '#c0392b',
    'STRANDED':    '#95a5a6',
}


def compute_metrics(sku_df: pd.DataFrame, demand_df: pd.DataFrame,
                    service_level: str = '95%') -> pd.DataFrame:
    """
    For each SKU compute:
      safety_stock, reorder_point, days_of_supply, sell_through_rate, status.

    Safety stock formula (statistical method):
      SS = Z × σ_demand × √(lead_time)
    Reorder point:
      ROP = avg_daily_demand × lead_time + SS
    """
    z = SERVICE_LEVELS[service_level]

    stats = demand_df.groupby('sku').agg(
        avg_daily_demand=('units_sold', 'mean'),
        std_daily_demand=('units_sold', 'std'),
        total_units_90d=('units_sold', 'sum'),
    ).reset_index()

    df = sku_df.merge(stats, on='sku')

    df['safety_stock'] = (
        z * df['std_daily_demand'] * np.sqrt(df['lead_time_days'])
    ).round(0).astype(int)

    df['reorder_point'] = (
        df['avg_daily_demand'] * df['lead_time_days'] + df['safety_stock']
    ).round(0).astype(int)

    df['days_of_supply'] = (df['current_stock'] / df['avg_daily_demand']).round(1)
    df['is_excess'] = df['days_of_supply'] > 90

    avg_inventory = (df['current_stock'] + df['total_units_90d']) / 2
    df['sell_through_rate'] = (df['total_units_90d'] / avg_inventory).round(2)

    df['status'] = df.apply(_status, axis=1)
    return df


def _status(row: pd.Series) -> str:
    if row['is_stranded']:
        return 'STRANDED'
    if row['current_stock'] == 0:
        return 'STOCKOUT'
    if row['current_stock'] < row['safety_stock']:
        return 'CRITICAL'
    if row['current_stock'] <= row['reorder_point']:
        return 'REORDER NOW'
    if row['is_excess']:
        return 'EXCESS'
    return 'OK'
