import pandas as pd
import plotly.graph_objects as go


def run_abc_analysis(sku_df: pd.DataFrame, demand_df: pd.DataFrame) -> pd.DataFrame:
    """Classify SKUs as A/B/C by 90-day revenue contribution."""
    revenue = (
        demand_df.groupby('sku')['units_sold'].sum()
        .reset_index()
        .merge(sku_df[['sku', 'product_name', 'price']], on='sku')
    )
    revenue['revenue_90d'] = revenue['units_sold'] * revenue['price']
    revenue = revenue.sort_values('revenue_90d', ascending=False).reset_index(drop=True)

    total = revenue['revenue_90d'].sum()
    revenue['revenue_pct'] = (revenue['revenue_90d'] / total * 100).round(1)
    revenue['cumulative_pct'] = revenue['revenue_pct'].cumsum().round(1)

    def _classify(cum: float) -> str:
        if cum <= 80:
            return 'A'
        if cum <= 95:
            return 'B'
        return 'C'

    revenue['abc_class'] = revenue['cumulative_pct'].apply(_classify)
    return revenue


def plot_pareto(abc_df: pd.DataFrame) -> go.Figure:
    """Pareto chart: bars by revenue %, line for cumulative %."""
    color_map = {'A': '#2ecc71', 'B': '#f39c12', 'C': '#e74c3c'}
    bar_colors = [color_map[c] for c in abc_df['abc_class']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=abc_df['product_name'],
        y=abc_df['revenue_pct'],
        name='Revenue share (%)',
        marker_color=bar_colors,
        text=abc_df['abc_class'],
        textposition='outside',
    ))

    fig.add_trace(go.Scatter(
        x=abc_df['product_name'],
        y=abc_df['cumulative_pct'],
        name='Cumulative (%)',
        mode='lines+markers',
        line=dict(color='#2c3e50', width=2),
        yaxis='y2',
    ))

    fig.add_hline(y=80, line_dash='dash', line_color='#7f8c8d',
                  annotation_text='80% — Class A cutoff', yref='y2')
    fig.add_hline(y=95, line_dash='dot', line_color='#7f8c8d',
                  annotation_text='95% — Class B cutoff', yref='y2')

    fig.update_layout(
        title='ABC Analysis — 90-Day Revenue Contribution',
        xaxis_title='Product',
        yaxis=dict(title='Revenue share (%)'),
        yaxis2=dict(title='Cumulative (%)', overlaying='y', side='right', range=[0, 108]),
        legend=dict(x=0.01, y=0.99),
        height=440,
        plot_bgcolor='white',
    )
    return fig
