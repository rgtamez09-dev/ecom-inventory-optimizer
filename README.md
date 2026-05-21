# 📦 ecom-inventory-optimizer

**Inventory optimization tool for Amazon FBA brands** — built with Python, Pandas, Plotly, and Streamlit.

Simulates the full inventory management workflow for a fictitious fitness accessories brand (**FlexCore**): ABC analysis, safety stock calculation, Amazon IPI Score monitoring, and a campaign readiness checker for the Ops × Growth coordination loop.

---

## 🚀 Live Demo

> [**Open the app →**](https://ecom-inventory-optimizer.streamlit.app) *(deploy link goes here after Streamlit Cloud setup)*

---

## The Problem

Amazon FBA brands face a permanent tension:

| Over-stock | Under-stock |
|---|---|
| Capital locked in warehouse | Lost sales, missed Buy Box |
| Higher storage fees | Amazon IPI Score drops |
| IPI Score penalized (>90 days supply) | Stockouts during campaigns |

This tool makes inventory decisions **data-driven and proactive** — especially the Ops × Growth coordination point: *can we launch this campaign given current stock levels?*

---

## Features

### 📊 Tab 1 — Inventory Overview
- Real-time status per SKU: `OK` / `REORDER NOW` / `CRITICAL` / `EXCESS` / `STRANDED`
- Days of supply with 90-day excess threshold and 30-day reorder zone highlighted
- Filter by ABC class

### 🅰️ Tab 2 — ABC Analysis
- Pareto chart of SKUs by 90-day revenue contribution
- Class A (80% revenue) vs. B vs. C — actionable strategy per tier

### 📈 Tab 3 — IPI Score Simulator
- Estimate your Amazon IPI Score based on the 4 known components
- Interactive sliders + gauge chart
- Specific advice for whichever component is dragging the score

### 🚀 Tab 4 — Campaign Readiness
- Input: SKU + demand uplift % + campaign duration
- Output: Safe ✅ / Warning ⚠️ / Danger 🚨 + units to order + order deadline
- Full stock breakdown: campaign demand + post-campaign buffer + safety stock

---

## Model Details

### Safety Stock (statistical method)
```
Safety Stock = Z × σ_demand × √(lead_time_days)
```
- Z factor: 1.65 (95% service level) / 2.05 (98%) / 2.58 (99%)
- Configurable from the sidebar

### Reorder Point
```
ROP = avg_daily_demand × lead_time + safety_stock
```

### Amazon IPI Score (approximation)
Amazon does not publish the exact formula. This tool uses a weighted approximation based on industry benchmarks:
```
IPI ≈ (sell_through_score × 0.35) + (excess_score × 0.35) 
    + (stranded_score × 0.15) + (instock_score × 0.15)  ×  1000
```
Thresholds: <400 = penalized | 400–549 = at risk | 550–699 = good | 700+ = excellent

---

## Tech Stack

```
Python 3.11+
pandas          — data manipulation
numpy           — statistical calculations
plotly          — interactive charts
streamlit       — web dashboard
```

---

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ecom-inventory-optimizer.git
cd ecom-inventory-optimizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## Project Structure

```
ecom-inventory-optimizer/
├── data/
│   └── simulate_data.py     # 8-SKU simulated demand (90 days, seasonality)
├── src/
│   ├── abc_analysis.py      # ABC classification + Pareto chart
│   ├── inventory_model.py   # Safety stock, ROP, days of supply, status
│   ├── ipi_simulator.py     # Amazon IPI Score estimator + gauge chart
│   └── campaign_checker.py  # Ops × Growth campaign readiness logic
├── app.py                   # Streamlit dashboard (4 tabs)
├── notebook/
│   └── inventory_analysis.ipynb  # Analytical narrative for portfolio
└── requirements.txt
```

---

## Replacing Simulated Data with Real Data

The `simulate_data.py` module returns two DataFrames: `sku_df` (master) and `demand_df` (daily sales history). To use real data, replace these with your own CSV files and ensure the same column names:

**sku_df columns:** `sku`, `product_name`, `price`, `cogs`, `lead_time_days`, `current_stock`, `is_stranded`

**demand_df columns:** `date`, `sku`, `units_sold`

---

## Author

**Roberto Galarza** — Operations & AI | [LinkedIn](https://linkedin.com/in/robertogalarza) | [Portfolio](https://robertogalarza.netlify.app)
