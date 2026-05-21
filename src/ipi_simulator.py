"""
Amazon IPI Score simulator.
Amazon does not publish the exact formula.
Weights are derived from industry benchmarks:
  Excess inventory and sell-through rate carry the most weight (~35% each).
  Stranded inventory and in-stock rate carry the remainder (~15% each).
"""
import plotly.graph_objects as go


def estimate_ipi(sell_through_rate: float, excess_pct: float,
                 stranded_pct: float, instock_rate: float) -> int:
    """
    Returns an estimated IPI score (0–1000).

    Args:
        sell_through_rate: units sold 90d / avg inventory (target >= 3.0)
        excess_pct:        % of units flagged as excess supply (target = 0%)
        stranded_pct:      % of units with no active listing (target = 0%)
        instock_rate:      % of days product was in stock (target = 100%)
    """
    sell_through_score = min(sell_through_rate / 3.0, 1.0)
    excess_score       = max(0.0, 1.0 - excess_pct / 50.0)
    stranded_score     = max(0.0, 1.0 - stranded_pct / 10.0)
    instock_score      = instock_rate / 100.0

    weighted = (
        sell_through_score * 0.35 +
        excess_score       * 0.35 +
        stranded_score     * 0.15 +
        instock_score      * 0.15
    )
    return min(round(weighted * 1000), 1000)


def ipi_label(score: int) -> tuple[str, str]:
    """Returns (label, hex_color) for a given IPI score."""
    if score >= 700:
        return '🟢 Excellent (700+)', '#2ecc71'
    if score >= 550:
        return '🟡 Good (550–699)', '#f39c12'
    if score >= 400:
        return '🟠 At Risk (400–549)', '#e67e22'
    return '🔴 Penalized (<400)', '#e74c3c'


def plot_gauge(score: int) -> go.Figure:
    label, color = ipi_label(score)
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=score,
        title={'text': f'Estimated IPI Score — {label}', 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 1000], 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.3},
            'steps': [
                {'range': [0,   400], 'color': '#fadbd8'},
                {'range': [400, 550], 'color': '#fdebd0'},
                {'range': [550, 700], 'color': '#fef9e7'},
                {'range': [700, 1000], 'color': '#eafaf1'},
            ],
            'threshold': {
                'line': {'color': '#e74c3c', 'width': 3},
                'thickness': 0.75,
                'value': 400,
            },
        },
    ))
    fig.update_layout(height=320, margin=dict(t=60, b=20))
    return fig


def ipi_advice(sell_through_rate: float, excess_pct: float,
               stranded_pct: float, instock_rate: float) -> list[str]:
    """Return actionable advice based on which components are underperforming."""
    tips = []
    if sell_through_rate < 3.0:
        tips.append(f"📦 **Sell-through rate is {sell_through_rate:.1f}** (target ≥ 3.0). "
                    "Run promotions or reduce restock quantities to increase velocity.")
    if excess_pct > 10:
        tips.append(f"⚠️ **{excess_pct:.0f}% of units are excess** (>90 days of supply). "
                    "Liquidate slow SKUs via FBA Liquidations or create a lightning deal.")
    if stranded_pct > 2:
        tips.append(f"🔗 **{stranded_pct:.1f}% stranded inventory**. "
                    "Go to Seller Central → Inventory → Fix Stranded Inventory immediately.")
    if instock_rate < 90:
        tips.append(f"📉 **In-stock rate is {instock_rate:.0f}%** (target ≥ 95%). "
                    "Increase reorder frequency or safety stock for top-selling SKUs.")
    if not tips:
        tips.append("✅ All components are healthy. Maintain current inventory strategy.")
    return tips
