import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_dashboard_preview():
    # Set dark theme colors matching live web app
    bg_color = '#0f172a'
    card_color = '#1e293b'
    border_color = '#334155'
    text_light = '#f8fafc'
    text_dim = '#94a3b8'

    fig = plt.figure(figsize=(12, 7.5), facecolor=bg_color)
    
    # 1. Header
    fig.text(0.05, 0.93, "Retail Sales Performance Dashboard", fontsize=18, fontweight='bold', color='#38bdf8')
    fig.text(0.05, 0.89, "End-to-End Analytics Pipeline Demonstration | Adarsh Sinha", fontsize=11, color=text_dim)

    # 2. KPI Cards
    kpis = [
        ("TOTAL REVENUE", "$18.11M", "#38bdf8", 0.05),
        ("TOTAL PROFIT", "$2.93M", "#4ade80", 0.28),
        ("PROFIT MARGIN %", "16.18%", "#f8fafc", 0.51),
        ("DISCOUNT LOSS (>40%)", "-$1.55M", "#f87171", 0.74)
    ]

    for title, val, col, x_pos in kpis:
        ax_kpi = fig.add_axes([x_pos, 0.70, 0.21, 0.14], facecolor=card_color)
        ax_kpi.set_xticks([])
        ax_kpi.set_yticks([])
        for spine in ax_kpi.spines.values():
            spine.set_color(border_color)
        ax_kpi.text(0.1, 0.65, title, fontsize=9, fontweight='bold', color=text_dim)
        ax_kpi.text(0.1, 0.20, val, fontsize=18, fontweight='bold', color=col)

    # 3. Chart 1: Profit Margin by Discount Tier
    ax1 = fig.add_axes([0.05, 0.22, 0.43, 0.40], facecolor=card_color)
    ax1.set_title("Profit Margin % by Discount Tier", fontsize=12, fontweight='bold', color=text_light, pad=12, loc='left')
    tiers = ['0%', '1-20%', '21-40%', '41-60%', '>60%']
    margins = [40.0, 29.34, 7.94, -20.00, -137.11]
    bar_colors = ['#4ade80', '#38bdf8', '#fbbf24', '#f87171', '#ef4444']
    
    bars = ax1.bar(tiers, margins, color=bar_colors, width=0.55)
    ax1.axhline(0, color='#64748b', linewidth=1)
    ax1.tick_params(colors=text_dim, labelsize=9)
    for spine in ax1.spines.values():
        spine.set_color(border_color)
    ax1.grid(axis='y', linestyle='--', alpha=0.3, color='#334155')

    # 4. Chart 2: Customer RFM Revenue Share
    ax2 = fig.add_axes([0.52, 0.22, 0.43, 0.40], facecolor=card_color)
    ax2.set_title("Customer RFM Segment Revenue Share ($)", fontsize=12, fontweight='bold', color=text_light, pad=12, loc='left')
    segments = ['At Risk ($7.33M)', 'Champions ($3.75M)', 'Loyal ($3.06M)', 'Lost ($2.44M)', 'Promising ($1.53M)']
    shares = [7.33, 3.75, 3.06, 2.44, 1.53]
    donut_colors = ['#c084fc', '#38bdf8', '#4ade80', '#f87171', '#fbbf24']
    
    wedges, texts, autotexts = ax2.pie(
        shares, labels=segments, autopct='%1.1f%%', startangle=140,
        colors=donut_colors, textprops=dict(color=text_light, fontsize=8),
        wedgeprops=dict(width=0.45, edgecolor=card_color)
    )
    for at in autotexts:
        at.set_color('#0f172a')
        at.set_weight('bold')
    for spine in ax2.spines.values():
        spine.set_color(border_color)

    # 5. Bottom Insights Banner
    ax_bot = fig.add_axes([0.05, 0.04, 0.90, 0.12], facecolor=card_color)
    ax_bot.set_xticks([])
    ax_bot.set_yticks([])
    for spine in ax_bot.spines.values():
        spine.set_color(border_color)
    
    ax_bot.text(0.02, 0.70, "Key Executive Findings & Recommendations", fontsize=10, fontweight='bold', color=text_light)
    ax_bot.text(0.02, 0.35, "• Discount Cap: Enforce 20% max discount cap to recover -$1.55M profit degradation on clearance sales.", fontsize=8.5, color=text_dim)
    ax_bot.text(0.02, 0.10, "• Customer Churn: 73% of customers are inactive (>180 days). Deploy automated re-engagement to At-Risk cohort.", fontsize=8.5, color=text_dim)

    # Save preview image
    output_path = "c:/Users/HP/Desktop/projects/retail-sales-dashboard/dashboard/dashboard_preview.png"
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor=bg_color)
    plt.close()
    print(f"Dashboard preview image saved at: {output_path}")

if __name__ == "__main__":
    generate_dashboard_preview()
