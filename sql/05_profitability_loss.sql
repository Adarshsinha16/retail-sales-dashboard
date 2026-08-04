-- QUERY 4: Profit Margin by Category & Top Loss-Making Products
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
