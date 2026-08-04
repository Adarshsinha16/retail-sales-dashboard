-- QUERY 1: Revenue by Region, Category, and Sub-Category with % Share
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
