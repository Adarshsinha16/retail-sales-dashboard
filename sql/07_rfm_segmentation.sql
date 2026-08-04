-- QUERY 6: RFM (Recency, Frequency, Monetary) Customer Segmentation
WITH max_ref_date AS (
    SELECT MAX(order_date) AS ref_date FROM fact_orders
),
rfm_metrics AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.segment,
        CAST(JULIANDAY((SELECT ref_date FROM max_ref_date)) - JULIANDAY(MAX(f.order_date)) AS INT) AS recency_days,
        COUNT(DISTINCT f.order_id) AS frequency,
        ROUND(SUM(f.sales), 2) AS monetary
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.customer_id, c.customer_name, c.segment
),
rfm_scores AS (
    SELECT 
        *,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_metrics
),
rfm_segmented AS (
    SELECT 
        *,
        CASE 
            WHEN (5 - r_score) >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
            WHEN (5 - r_score) >= 3 AND f_score >= 2 THEN 'Loyal Customers'
            WHEN (5 - r_score) <= 2 AND f_score >= 3 THEN 'At Risk / Need Attention'
            WHEN (5 - r_score) <= 2 AND f_score <= 2 THEN 'Lost Customers'
            ELSE 'Promising / Recent'
        END AS customer_segment
    FROM rfm_scores
)
SELECT 
    customer_segment,
    COUNT(customer_id) AS customer_count,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(frequency), 1) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary_spend,
    ROUND(SUM(monetary), 2) AS total_segment_revenue
FROM rfm_segmented
GROUP BY customer_segment
ORDER BY total_segment_revenue DESC;
