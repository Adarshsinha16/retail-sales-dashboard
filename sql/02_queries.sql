-- ============================================================================
-- Phase 2: Portfolio Analytical SQL Queries
-- Database: PostgreSQL / SQLite Compatible
-- Author: Data Analyst Portfolio
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: Revenue by Region, Category, and Sub-Category with % Share
-- ----------------------------------------------------------------------------
WITH region_cat_sales AS (
    SELECT 
        r.region_name,
        p.category,
        p.sub_category,
        ROUND(SUM(f.sales), 2) AS total_revenue,
        ROUND(SUM(f.profit), 2) AS total_profit,
        COUNT(DISTINCT f.order_id) AS total_orders
    FROM fact_orders f
    JOIN dim_regions r ON f.region_id = r.region_id
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY r.region_name, p.category, p.sub_category
)
SELECT 
    region_name,
    category,
    sub_category,
    total_revenue,
    total_profit,
    total_orders,
    ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER(), 2) AS pct_of_global_revenue,
    ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER(PARTITION BY region_name), 2) AS pct_of_region_revenue
FROM region_cat_sales
ORDER BY region_name, total_revenue DESC;

-- ----------------------------------------------------------------------------
-- QUERY 2: Monthly Revenue Trend with MoM % Growth (Window Function: LAG)
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- QUERY 3: Top 10 Customers by Lifetime Revenue & Cumulative Share
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- QUERY 4: Profit Margin by Category & Top Loss-Making Products
-- ----------------------------------------------------------------------------
-- Part 4A: Category Margin Overview
SELECT 
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.profit) * 100.0 / NULLIF(SUM(f.sales), 0), 2) AS profit_margin_pct,
    ROUND(AVG(f.discount) * 100, 2) AS avg_discount_pct
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.category, p.sub_category
ORDER BY profit_margin_pct ASC;

-- Part 4B: Top 10 Loss-Making Products
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS net_profit_loss,
    ROUND(AVG(f.discount) * 100, 2) AS avg_discount_given,
    COUNT(f.fact_id) AS items_sold
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category
HAVING SUM(f.profit) < 0
ORDER BY net_profit_loss ASC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- QUERY 5: Customer Churn & Cohort Retention Analysis
-- Definition: Churned = No purchase in the last 180 days relative to max dataset date
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- QUERY 6: RFM (Recency, Frequency, Monetary) Customer Segmentation
-- Using NTILE(4) to rank customers across RFM dimensions
-- ----------------------------------------------------------------------------
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
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score, -- Lower recency days = Higher R score (inverted)
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_metrics
),
rfm_segmented AS (
    SELECT 
        *,
        (5 - r_score) AS r_rank, -- Re-invert so 4 is Best Recency
        f_score AS f_rank,
        m_score AS m_rank,
        ((5 - r_score) + f_score + m_score) AS rfm_total_score,
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

-- ----------------------------------------------------------------------------
-- QUERY 7: Discount Impact on Profitability (Discount Tier Correlation)
-- ----------------------------------------------------------------------------
WITH discount_tiers AS (
    SELECT 
        fact_id,
        sales,
        profit,
        discount,
        profit_margin,
        CASE 
            WHEN discount = 0.0 THEN '0% (No Discount)'
            WHEN discount > 0.0 AND discount <= 0.2 THEN '1% - 20% (Low)'
            WHEN discount > 0.2 AND discount <= 0.4 THEN '21% - 40% (Moderate)'
            WHEN discount > 0.4 AND discount <= 0.6 THEN '41% - 60% (High)'
            ELSE '> 60% (Extreme Clearance)'
        END AS discount_tier
    FROM fact_orders
)
SELECT 
    discount_tier,
    COUNT(fact_id) AS total_items_sold,
    ROUND(SUM(sales), 2) AS gross_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(AVG(profit_margin) * 100, 2) AS avg_profit_margin_pct,
    ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS overall_tier_margin_pct
FROM discount_tiers
GROUP BY discount_tier
ORDER BY MIN(discount) ASC;
