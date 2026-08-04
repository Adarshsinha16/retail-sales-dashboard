-- QUERY 7: Discount Impact on Profitability (Discount Tier Correlation)
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
