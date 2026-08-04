-- QUERY 5: Customer Churn & Cohort Retention Analysis
-- Definition: Churned = No purchase in the last 180 days relative to max dataset date
WITH dataset_max_date AS (
    SELECT MAX(order_date) AS max_date FROM fact_orders
),
customer_recency AS (
    SELECT 
        c.customer_id,
        c.segment,
        r.region_name,
        MAX(f.order_date) AS last_order_date,
        (JULIANDAY((SELECT max_date FROM dataset_max_date)) - JULIANDAY(MAX(f.order_date))) AS days_since_last_order,
        COUNT(DISTINCT f.order_id) AS order_frequency,
        ROUND(SUM(f.sales), 2) AS total_spend
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    JOIN dim_regions r ON f.region_id = r.region_id
    GROUP BY c.customer_id, c.segment, r.region_name
),
churn_flagged AS (
    SELECT 
        *,
        CASE WHEN days_since_last_order > 180 THEN 1 ELSE 0 END AS is_churned
    FROM customer_recency
)
SELECT 
    region_name,
    segment,
    COUNT(customer_id) AS total_customers,
    SUM(is_churned) AS churned_customers,
    ROUND(SUM(is_churned) * 100.0 / COUNT(customer_id), 2) AS churn_rate_pct,
    ROUND(AVG(days_since_last_order), 0) AS avg_days_since_purchase
FROM churn_flagged
GROUP BY region_name, segment
ORDER BY churn_rate_pct DESC;
