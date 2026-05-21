from datetime import datetime, timedelta
import pandas as pd


def check_readiness(inv_df: pd.DataFrame, sku: str,
                    uplift_pct: float, campaign_days: int) -> dict:
    """
    Evaluate whether current FBA stock can support a sales campaign.

    Logic:
      demand_campaign   = avg_daily_demand × (1 + uplift) × campaign_days
      demand_post       = avg_daily_demand × lead_time   (buffer until restock)
      stock_needed      = demand_campaign + demand_post + safety_stock
      units_to_order    = max(0, stock_needed - current_stock)
      order_deadline    = today + (lead_time - 7 days)  ← 1-week safety margin
    """
    row = inv_df[inv_df['sku'] == sku].iloc[0]

    avg_demand    = row['avg_daily_demand']
    current_stock = row['current_stock']
    lead_time     = row['lead_time_days']
    safety_stock  = row['safety_stock']

    campaign_demand   = avg_demand * (1 + uplift_pct / 100) * campaign_days
    post_campaign_buf = avg_demand * lead_time
    stock_needed      = campaign_demand + post_campaign_buf + safety_stock
    units_to_order    = max(0, round(stock_needed - current_stock))

    days_until_sto = (
        current_stock / (avg_demand * (1 + uplift_pct / 100))
        if avg_demand * (1 + uplift_pct / 100) > 0
        else 999
    )

    deadline_days  = int(max(0, lead_time - 7))
    order_deadline = (datetime.today() + timedelta(days=deadline_days)).strftime('%d %b %Y')

    if stock_needed <= current_stock:
        status  = 'SAFE'
        message = (f"✅ **Safe to launch.** Current stock of {int(current_stock):,} units covers "
                   f"campaign demand ({int(campaign_demand):,}) + {lead_time}-day restock buffer "
                   f"({int(post_campaign_buf):,}) + safety stock ({int(safety_stock):,}).")
    elif days_until_sto < campaign_days:
        status  = 'DANGER'
        message = (f"🚨 **Do NOT launch yet.** Stock runs out in **{days_until_sto:.0f} days** "
                   f"— before the {campaign_days}-day campaign ends. "
                   f"Order **{units_to_order:,} units** by **{order_deadline}**.")
    else:
        status  = 'WARNING'
        message = (f"⚠️ **Can launch, but act now.** Stock lasts through the campaign "
                   f"but will hit critical levels during restock window. "
                   f"Order **{units_to_order:,} units** by **{order_deadline}**.")

    return {
        'status':              status,
        'message':             message,
        'campaign_demand':     round(campaign_demand),
        'post_campaign_buffer': round(post_campaign_buf),
        'safety_stock':        int(safety_stock),
        'stock_needed':        round(stock_needed),
        'current_stock':       int(current_stock),
        'units_to_order':      units_to_order,
        'order_deadline':      order_deadline,
        'days_until_stockout': round(days_until_sto, 1),
    }
