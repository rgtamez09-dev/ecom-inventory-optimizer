import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data.simulate_data import generate_data
from src.abc_analysis import run_abc_analysis, plot_pareto
from src.inventory_model import compute_metrics, STATUS_COLOR, SERVICE_LEVELS
from src.ipi_simulator import estimate_ipi, plot_gauge, ipi_advice
from src.campaign_checker import check_readiness

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='FlexCore — Inventory Optimizer',
    page_icon='📦',
    layout='wide',
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    sku_df, demand_df = generate_data()
    return sku_df, demand_df

sku_df, demand_df = load()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image('https://via.placeholder.com/200x60/2c3e50/ffffff?text=FlexCore', width=200)
    st.markdown('### Settings')
    service_level = st.selectbox('Service Level (Safety Stock)', list(SERVICE_LEVELS.keys()), index=0)
    st.markdown('---')
    st.markdown(
        '**FlexCore** — Fitness accessories brand selling exclusively via Amazon FBA.\n\n'
        'This dashboard simulates real-time inventory decisions for 8 SKUs sourced from Asia '
        '(lead times 25–45 days).\n\n'
        '_Built with Python · Pandas · Plotly · Streamlit_'
    )

inv_df = compute_metrics(sku_df, demand_df, service_level)
abc_df = run_abc_analysis(sku_df, demand_df)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    '📊 Inventory Overview',
    '🅰️ ABC Analysis',
    '📈 IPI Score Simulator',
    '🚀 Campaign Readiness',
])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — INVENTORY OVERVIEW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.title('📦 Inventory Overview — FlexCore FBA')

    # KPI cards
    counts = inv_df['status'].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('✅ OK',          counts.get('OK', 0))
    c2.metric('🟡 Reorder Now', counts.get('REORDER NOW', 0))
    c3.metric('🔴 Critical',    counts.get('CRITICAL', 0) + counts.get('STOCKOUT', 0))
    c4.metric('🟣 Excess',      counts.get('EXCESS', 0))

    st.markdown('---')

    # Filter by ABC class
    abc_filter = st.multiselect(
        'Filter by ABC Class',
        options=['A', 'B', 'C'],
        default=['A', 'B', 'C'],
    )
    abc_map = dict(zip(abc_df['sku'], abc_df['abc_class']))
    display_df = inv_df.copy()
    display_df['abc_class'] = display_df['sku'].map(abc_map)
    display_df = display_df[display_df['abc_class'].isin(abc_filter)]

    # Display table with color-coded status
    cols_show = ['sku', 'product_name', 'abc_class', 'current_stock',
                 'days_of_supply', 'safety_stock', 'reorder_point',
                 'sell_through_rate', 'status']

    def color_status(val):
        color = STATUS_COLOR.get(val, '#ffffff')
        return f'background-color: {color}22; color: {color}; font-weight: bold'

    styled = (
        display_df[cols_show]
        .rename(columns={
            'sku': 'SKU', 'product_name': 'Product', 'abc_class': 'Class',
            'current_stock': 'Stock', 'days_of_supply': 'Days Supply',
            'safety_stock': 'Safety Stock', 'reorder_point': 'Reorder Point',
            'sell_through_rate': 'Sell-Through', 'status': 'Status',
        })
        .style.applymap(color_status, subset=['Status'])
        .format({'Days Supply': '{:.1f}', 'Sell-Through': '{:.2f}'})
    )
    st.dataframe(styled, use_container_width=True)

    # Days-of-supply bar chart
    st.markdown('#### Days of Supply per SKU')
    fig = go.Figure()
    for _, row in display_df.iterrows():
        fig.add_trace(go.Bar(
            x=[row['product_name']],
            y=[row['days_of_supply']],
            marker_color=STATUS_COLOR.get(row['status'], '#cccccc'),
            name=row['status'],
            showlegend=False,
            text=f"{row['days_of_supply']:.0f}d",
            textposition='outside',
        ))
    fig.add_hline(y=90, line_dash='dash', line_color='#e74c3c',
                  annotation_text='90-day excess threshold')
    fig.add_hline(y=30, line_dash='dot', line_color='#f39c12',
                  annotation_text='30-day reorder zone')
    fig.update_layout(height=380, yaxis_title='Days of Supply',
                      xaxis_title='', plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — ABC ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.title('🅰️ ABC Analysis — Revenue Prioritization')
    st.markdown(
        'SKUs classified by 90-day revenue contribution. '
        '**Class A** = top 80% of revenue → highest priority for stock availability. '
        '**Class C** = bottom 5% → liquidation candidates if excess stock builds up.'
    )

    st.plotly_chart(plot_pareto(abc_df), use_container_width=True)

    st.markdown('#### Classification Detail')
    show_abc = abc_df[['sku', 'product_name', 'units_sold', 'revenue_90d',
                        'revenue_pct', 'cumulative_pct', 'abc_class']].rename(columns={
        'sku': 'SKU', 'product_name': 'Product', 'units_sold': 'Units Sold (90d)',
        'revenue_90d': 'Revenue (€)', 'revenue_pct': 'Share (%)',
        'cumulative_pct': 'Cumulative (%)', 'abc_class': 'Class',
    })

    def color_class(val):
        return {'A': 'background-color: #d5f5e3', 'B': 'background-color: #fef9e7',
                'C': 'background-color: #fadbd8'}.get(val, '')

    st.dataframe(
        show_abc.style
        .applymap(color_class, subset=['Class'])
        .format({'Revenue (€)': '€{:.2f}', 'Share (%)': '{:.1f}%', 'Cumulative (%)': '{:.1f}%'}),
        use_container_width=True,
    )

    st.markdown('#### Strategic Recommendations by Class')
    st.markdown("""
| Class | SKUs | Action |
|---|---|---|
| **A** | Yoga Mat Pro, Resistance Bands Set, Foam Roller, Knee Sleeves | Never stockout. Maintain 60+ days supply. Prioritize in reorders. |
| **B** | Gym Gloves, Shaker Bottle | Keep 30–45 days. Monitor closely but don't over-invest. |
| **C** | Jump Rope Speed, Lifting Belt | Liquidate if excess. Discontinue if margin doesn't justify complexity. |
""")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — IPI SCORE SIMULATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.title('📈 Amazon IPI Score Simulator')
    st.markdown(
        'The **Inventory Performance Index** (0–1,000) determines your FBA storage capacity. '
        'Falling below **400** triggers storage restrictions and surcharges. '
        'Adjust the sliders to explore how each component impacts your score.'
    )

    # Compute defaults from actual data
    total_units = inv_df['current_stock'].sum() + inv_df['total_units_90d'].sum()
    excess_units = inv_df.loc[inv_df['is_excess'], 'current_stock'].sum()
    stranded_units = inv_df.loc[inv_df['is_stranded'], 'current_stock'].sum()
    avg_str = inv_df['sell_through_rate'].mean()

    default_excess_pct   = round(excess_units / total_units * 100, 1) if total_units > 0 else 0
    default_stranded_pct = round(stranded_units / total_units * 100, 1) if total_units > 0 else 0

    col_sliders, col_gauge = st.columns([1, 1])

    with col_sliders:
        st.markdown('#### Adjust IPI Components')
        sell_through = st.slider('Sell-Through Rate (target ≥ 3.0)', 0.0, 5.0, float(round(avg_str, 1)), 0.1,
                                 help='Units sold in 90d ÷ avg units stored')
        excess_pct   = st.slider('Excess Inventory (%)', 0.0, 50.0, default_excess_pct, 0.5,
                                 help='% of total units with >90 days of supply')
        stranded_pct = st.slider('Stranded Inventory (%)', 0.0, 20.0, default_stranded_pct, 0.5,
                                 help='% of units with no active listing')
        instock_rate = st.slider('In-Stock Rate (%)', 0.0, 100.0, 90.0, 1.0,
                                 help='% of days products were available for purchase')

    score = estimate_ipi(sell_through, excess_pct, stranded_pct, instock_rate)

    with col_gauge:
        st.plotly_chart(plot_gauge(score), use_container_width=True)

    st.markdown('#### What to Fix')
    for tip in ipi_advice(sell_through, excess_pct, stranded_pct, instock_rate):
        st.markdown(f'- {tip}')

    st.markdown('---')
    st.markdown("""
#### IPI Score Reference
| Score | Status | What happens |
|---|---|---|
| 700+ | 🟢 Excellent | No restrictions, maximum FBA capacity |
| 550–699 | 🟡 Good | Industry benchmark for healthy inventory management |
| 400–549 | 🟠 At Risk | No penalty yet — take corrective action |
| < 400 | 🔴 Penalized | Storage limit reduced + surcharge up to $10/ft³ |
""")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — CAMPAIGN READINESS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.title('🚀 Campaign Readiness — Ops × Growth')
    st.markdown(
        'Before Growth launches a promotion, discount, or external campaign, '
        'Ops must confirm that stock covers the demand spike **plus** the restock lead time. '
        'This tool makes that decision data-driven in seconds.'
    )

    col_in, col_out = st.columns([1, 1])

    with col_in:
        st.markdown('#### Campaign Parameters')
        sku_options = inv_df[['sku', 'product_name']].copy()
        sku_options['label'] = sku_options['sku'] + ' — ' + sku_options['product_name']
        selected_label = st.selectbox('Select SKU', sku_options['label'].tolist())
        selected_sku   = selected_label.split(' — ')[0]

        uplift_pct    = st.slider('Expected demand uplift (%)', 10, 200, 40, 5,
                                  help='How much more than baseline demand do you expect during the campaign?')
        campaign_days = st.slider('Campaign duration (days)', 1, 30, 7)

        st.markdown('---')
        row = inv_df[inv_df['sku'] == selected_sku].iloc[0]
        st.markdown(f"""
**Current snapshot — {selected_sku}**
- Stock in FBA: **{int(row['current_stock']):,} units**
- Avg. daily demand: **{row['avg_daily_demand']:.1f} units/day**
- Days of supply: **{row['days_of_supply']:.0f} days**
- Lead time: **{int(row['lead_time_days'])} days**
- Safety stock: **{int(row['safety_stock'])} units**
""")

    result = check_readiness(inv_df, selected_sku, uplift_pct, campaign_days)

    with col_out:
        st.markdown('#### Readiness Assessment')

        status_bg = {'SAFE': '#d5f5e3', 'WARNING': '#fef9e7', 'DANGER': '#fadbd8'}
        st.markdown(
            f"<div style='background:{status_bg[result['status']]}; padding:16px; "
            f"border-radius:8px; font-size:15px'>{result['message']}</div>",
            unsafe_allow_html=True,
        )

        st.markdown('---')
        st.markdown('#### Stock Breakdown')
        breakdown = pd.DataFrame({
            'Component': ['Campaign demand', 'Post-campaign buffer', 'Safety stock', 'Total needed', 'Current stock', 'Gap (order qty)'],
            'Units': [
                result['campaign_demand'],
                result['post_campaign_buffer'],
                result['safety_stock'],
                result['stock_needed'],
                result['current_stock'],
                result['units_to_order'],
            ],
        })
        st.dataframe(breakdown, use_container_width=True, hide_index=True)

        if result['units_to_order'] > 0:
            st.warning(f"📅 Order deadline: **{result['order_deadline']}** "
                       f"(lead time: {int(row['lead_time_days'])} days, with 7-day safety margin)")
