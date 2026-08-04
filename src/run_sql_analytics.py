import sqlite3
import pandas as pd

def run_analytical_queries(db_path):
    conn = sqlite3.connect(db_path)
    print("=" * 70)
    print("EXECUTING PHASE 2 ANALYTICAL SQL QUERIES")
    print("=" * 70)

    # 1. Revenue Breakdown
    q1 = """
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
        ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER(), 2) AS pct_global_rev
    FROM region_cat_sales
    ORDER BY total_revenue DESC
    LIMIT 5;
    """
    print("\n--- [Query 1: Top 5 Region & Category Revenue Combinations] ---")
    df1 = pd.read_sql(q1, conn)
    print(df1.to_string(index=False))

    # 2. Monthly Revenue Trend with MoM Growth
    q2 = """
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
        ) AS mom_growth_pct
    FROM monthly_revenue
    ORDER BY year_month DESC
    LIMIT 6;
    """
    print("\n--- [Query 2: Recent 6 Months MoM Revenue Growth Trend] ---")
    df2 = pd.read_sql(q2, conn)
    print(df2.to_string(index=False))

    # 3. Top Customers
    q3 = """
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
    )
    SELECT 
        customer_id,
        customer_name,
        segment,
        total_orders,
        lifetime_revenue,
        lifetime_profit,
        DENSE_RANK() OVER (ORDER BY lifetime_revenue DESC) AS revenue_rank
    FROM customer_revenue
    LIMIT 5;
    """
    print("\n--- [Query 3: Top 5 Customers by Lifetime Revenue] ---")
    df3 = pd.read_sql(q3, conn)
    print(df3.to_string(index=False))

    # 4. Profitability & Loss Products
    q4 = """
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        ROUND(SUM(f.sales), 2) AS total_sales,
        ROUND(SUM(f.profit), 2) AS net_profit_loss,
        ROUND(AVG(f.discount) * 100, 2) AS avg_discount_given
    FROM fact_orders f
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category
    HAVING SUM(f.profit) < 0
    ORDER BY net_profit_loss ASC
    LIMIT 5;
    """
    print("\n--- [Query 4: Top 5 Severe Loss-Making Products] ---")
    df4 = pd.read_sql(q4, conn)
    print(df4.to_string(index=False))

    # 5. Customer Churn Analysis
    q5 = """
    WITH dataset_max_date AS (
        SELECT MAX(order_date) AS max_date FROM fact_orders
    ),
    customer_recency AS (
        SELECT 
            c.customer_id,
            r.region_name,
            MAX(f.order_date) AS last_order_date,
            (JULIANDAY((SELECT max_date FROM dataset_max_date)) - JULIANDAY(MAX(f.order_date))) AS days_since_last_order
        FROM fact_orders f
        JOIN dim_customers c ON f.customer_id = c.customer_id
        JOIN dim_regions r ON f.region_id = r.region_id
        GROUP BY c.customer_id, r.region_name
    ),
    churn_flagged AS (
        SELECT *, CASE WHEN days_since_last_order > 180 THEN 1 ELSE 0 END AS is_churned FROM customer_recency
    )
    SELECT 
        region_name,
        COUNT(customer_id) AS total_customers,
        SUM(is_churned) AS churned_customers,
        ROUND(SUM(is_churned) * 100.0 / COUNT(customer_id), 2) AS churn_rate_pct
    FROM churn_flagged
    GROUP BY region_name
    ORDER BY churn_rate_pct DESC;
    """
    print("\n--- [Query 5: Customer Churn Rate by Region (>180 Days Inactive)] ---")
    df5 = pd.read_sql(q5, conn)
    print(df5.to_string(index=False))

    # 6. RFM Segmentation
    q6 = """
    WITH max_ref_date AS (
        SELECT MAX(order_date) AS ref_date FROM fact_orders
    ),
    rfm_metrics AS (
        SELECT 
            c.customer_id,
            CAST(JULIANDAY((SELECT ref_date FROM max_ref_date)) - JULIANDAY(MAX(f.order_date)) AS INT) AS recency_days,
            COUNT(DISTINCT f.order_id) AS frequency,
            ROUND(SUM(f.sales), 2) AS monetary
        FROM fact_orders f
        JOIN dim_customers c ON f.customer_id = c.customer_id
        GROUP BY c.customer_id
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
        ROUND(SUM(monetary), 2) AS total_segment_revenue
    FROM rfm_segmented
    GROUP BY customer_segment
    ORDER BY total_segment_revenue DESC;
    """
    print("\n--- [Query 6: RFM Customer Segment Summary] ---")
    df6 = pd.read_sql(q6, conn)
    print(df6.to_string(index=False))

    # 7. Discount Impact
    q7 = """
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
        ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS tier_margin_pct
    FROM discount_tiers
    GROUP BY discount_tier
    ORDER BY MIN(discount) ASC;
    """
    print("\n--- [Query 7: Discount Tier Impact on Profitability] ---")
    df7 = pd.read_sql(q7, conn)
    print(df7.to_string(index=False))

    conn.close()
    print("\n[SUCCESS] All 7 Analytical SQL Queries Executed Successfully!")

if __name__ == "__main__":
    run_analytical_queries("c:/Users/HP/Desktop/projects/retail-sales-dashboard/sales_dashboard.db")
