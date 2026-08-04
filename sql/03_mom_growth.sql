-- QUERY 2: Monthly Revenue Trend with MoM % Growth (Window Function: LAG)
WITH monthly_revenue AS (
    SELECT 
        STRFTIME('%Y-%m', order_date) AS year_month,
        ROUND(SUM(sales), 2) AS current_month_revenue,
        ROUND(SUM(profit), 2) AS current_month_profit,
        COUNT(DISTINCT order_id) AS total_orders
    FROM fact_orders
    GROUP BY STRFTIME('%Y-%m', order_date)
)
SELECT 
    year_month,
    current_month_revenue,
    LAG(current_month_revenue, 1) OVER (ORDER BY year_month) AS prior_month_revenue,
    ROUND(
        (current_month_revenue - LAG(current_month_revenue, 1) OVER (ORDER BY year_month)) * 100.0 / 
        NULLIF(LAG(current_month_revenue, 1) OVER (ORDER BY year_month), 0), 2
    ) AS mom_growth_pct,
    current_month_profit,
    total_orders
FROM monthly_revenue
ORDER BY year_month;
