-- QUERY 3: Top 10 Customers by Lifetime Revenue & Cumulative Share
WITH customer_revenue AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.segment,
        COUNT(DISTINCT f.order_id) AS total_orders,
        ROUND(SUM(f.sales), 2) AS lifetime_revenue,
        ROUND(SUM(f.profit), 2) AS lifetime_profit
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.customer_id, c.customer_name, c.segment
),
ranked_customers AS (
    SELECT 
        customer_id,
        customer_name,
        segment,
        total_orders,
        lifetime_revenue,
        lifetime_profit,
        DENSE_RANK() OVER (ORDER BY lifetime_revenue DESC) AS revenue_rank,
        ROUND(SUM(lifetime_revenue) OVER (ORDER BY lifetime_revenue DESC) * 100.0 / SUM(lifetime_revenue) OVER (), 2) AS cumulative_revenue_pct
    FROM customer_revenue
)
SELECT * 
FROM ranked_customers
WHERE revenue_rank <= 10;
