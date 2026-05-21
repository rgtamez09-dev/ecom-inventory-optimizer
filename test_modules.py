import sys
sys.stdout.reconfigure(encoding='utf-8')

from data.simulate_data import generate_data
from src.abc_analysis import run_abc_analysis
from src.inventory_model import compute_metrics
from src.campaign_checker import check_readiness
from src.ipi_simulator import estimate_ipi

sku_df, demand_df = generate_data()
inv_df = compute_metrics(sku_df, demand_df, "95%")

print("=== INVENTORY STATUS ===")
cols = ["sku", "product_name", "current_stock", "days_of_supply",
        "safety_stock", "reorder_point", "status"]
print(inv_df[cols].to_string(index=False))

print("\n=== ABC ANALYSIS ===")
abc = run_abc_analysis(sku_df, demand_df)
print(abc[["sku", "product_name", "revenue_90d", "cumulative_pct", "abc_class"]].to_string(index=False))

print("\n=== IPI SCORE (current portfolio) ===")
total = inv_df["current_stock"].sum() + inv_df["total_units_90d"].sum()
excess = inv_df.loc[inv_df["is_excess"], "current_stock"].sum()
stranded = inv_df.loc[inv_df["is_stranded"], "current_stock"].sum()
avg_str = inv_df["sell_through_rate"].mean()
score = estimate_ipi(avg_str, excess/total*100, stranded/total*100, 90)
print(f"Estimated IPI: {score}")

print("\n=== CAMPAIGN CHECK: FC-001 +40% uplift 7 days ===")
result = check_readiness(inv_df, "FC-001", 40, 7)
print(result["message"])
print("Units to order:", result["units_to_order"])

print("\n=== VERIFICATION: Logical correctness ===")
excess_skus = inv_df[inv_df["status"] == "EXCESS"]["sku"].tolist()
critical_skus = inv_df[inv_df["status"].isin(["CRITICAL", "STOCKOUT"])]["sku"].tolist()
print(f"Excess SKUs (>90d supply): {excess_skus}")
print(f"Critical SKUs: {critical_skus}")
print(f"FC-002 days_of_supply: {inv_df[inv_df['sku']=='FC-002']['days_of_supply'].values[0]:.1f} (expected >90)")
print(f"FC-004 days_of_supply: {inv_df[inv_df['sku']=='FC-004']['days_of_supply'].values[0]:.1f} (expected <10)")
print("All checks passed." if excess_skus and critical_skus else "WARNING: Check data setup")
