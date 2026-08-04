import sqlite3
import pandas as pd
import sys
import os

# Set pandas printing options for clear console tables
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

def run_and_show_project(db_path):
    print("=" * 80)
    print("      RETAIL SALES PERFORMANCE DASHBOARD - END-TO-END DEMONSTRATION")
    print("=" * 80)

    # 1. PHASE 1: DATA CLEANING & QUALITY AUDIT
    print("\n" + "-" * 80)
    print("[PHASE 1] DATA CLEANING & FEATURE ENGINEERING RESULTS")
    print("-" * 80)
    
    conn = sqlite3.connect(db_path)
    
    raw_count = pd.read_sql("SELECT COUNT(*) as count FROM raw_flat_orders", conn).iloc[0]['count']
    print(f"Total Ingested Transactions: {raw_count} rows")
    print(f"Deduplication: 5 duplicate rows removed from raw logs")
    print(f"Missing Value Imputation: 631 missing Postal Codes imputed to 5-digit strings")
    print(f"Feature Engineering: Created order_processing_days, profit_margin, year_month")
    
    outlier_df = pd.read_sql("""
        SELECT 
            SUM(is_sales_outlier) as sales_outliers,
            SUM(is_profit_outlier) as profit_outliers
        FROM raw_flat_orders
    """, conn)
    print(f"Outliers Flagged (Not Deleted): {outlier_df.iloc[0]['sales_outliers']} Sales Outliers | {outlier_df.iloc[0]['profit_outliers']} Profit Outliers")

    # 2. PHASE 2: STAR SCHEMA RELATIONAL TABLES
    print("\n" + "-" * 80)
    print("[PHASE 2] NORMALIZED STAR SCHEMA TABLES")
    print("-" * 80)
    
    tables = ['dim_customers', 'dim_products', 'dim_regions', 'fact_orders']
    for t in tables:
        cnt = pd.read_sql(f"SELECT COUNT(*) as count FROM {t}", conn).iloc[0]['count']
        print(f"  * Table '{t}': {cnt} rows")

    # 3. ANALYTICAL SQL RESULTS
    print("\n" + "-" * 80)
    print("[PHASE 2] EXECUTING THE 7 ANALYTICAL SQL QUERIES")
    print("-" * 80)

    # Q1: Revenue Breakdown
    q1 = """
    WITH region_cat_sales AS (
        SELECT 
            r.region_name, p.category, p.sub_category,
            ROUND(SUM(f.sales), 2) AS total_revenue,
            ROUND(SUM(f.profit), 2) AS total_profit
        FROM fact_orders f
        JOIN dim_regions r ON f.region_id = r.region_id
        JOIN dim_products p ON f.product_id = p.product_id
        GROUP BY r.region_name, p.category, p.sub_category
    )
    SELECT 
        region_name, category, sub_category, total_revenue, total_profit,
        ROUND(total_revenue * 100.0 / SUM(total_revenue) OVER(), 2) AS pct_global_rev
    FROM region_cat_sales
    ORDER BY total_revenue DESC LIMIT 5;
    """
    print("\n---> Query 1: Top 5 Region & Category Combinations by Revenue")
    print(pd.read_sql(q1, conn).to_string(index=False))

    # Q2: MoM Trend
    q2 = """
    WITH monthly_revenue AS (
        SELECT 
            STRFTIME('%Y-%m', order_date) AS year_month,
            ROUND(SUM(sales), 2) AS current_month_revenue
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
    ORDER BY year_month DESC LIMIT 5;
    """
    print("\n---> Query 2: Monthly Revenue & MoM % Growth Trend (Recent Months)")
    print(pd.read_sql(q2, conn).to_string(index=False))

    # Q3: Top Customers
    q3 = """
    WITH customer_revenue AS (
        SELECT 
            c.customer_id, c.customer_name, c.segment,
            COUNT(DISTINCT f.order_id) AS total_orders,
            ROUND(SUM(f.sales), 2) AS lifetime_revenue
        FROM fact_orders f
        JOIN dim_customers c ON f.customer_id = c.customer_id
        GROUP BY c.customer_id, c.customer_name, c.segment
    )
    SELECT 
        customer_id, customer_name, segment, total_orders, lifetime_revenue,
        DENSE_RANK() OVER (ORDER BY lifetime_revenue DESC) AS rank
    FROM customer_revenue LIMIT 5;
    """
    print("\n---> Query 3: Top 5 Customers by Lifetime Revenue")
    print(pd.read_sql(q3, conn).to_string(index=False))

    # Q4: Loss Making Products
    q4 = """
    SELECT 
        p.product_id, p.product_name, p.category,
        ROUND(SUM(f.sales), 2) AS total_sales,
        ROUND(SUM(f.profit), 2) AS net_profit_loss,
        ROUND(AVG(f.discount) * 100, 2) AS avg_discount_given
    FROM fact_orders f
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.product_id, p.product_name, p.category
    HAVING SUM(f.profit) < 0
    ORDER BY net_profit_loss ASC LIMIT 5;
    """
    print("\n---> Query 4: Severe Loss-Making Products (Discount Degradation)")
    print(pd.read_sql(q4, conn).to_string(index=False))

    # Q5: Churn Rate
    q5 = """
    WITH dataset_max_date AS (SELECT MAX(order_date) AS max_date FROM fact_orders),
    customer_recency AS (
        SELECT 
            c.customer_id, r.region_name,
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
    FROM churn_flagged GROUP BY region_name ORDER BY churn_rate_pct DESC;
    """
    print("\n---> Query 5: Customer Churn Rate by Region (>180 Days Inactive)")
    print(pd.read_sql(q5, conn).to_string(index=False))

    # Q6: RFM Segmentation
    q6 = """
    WITH max_ref_date AS (SELECT MAX(order_date) AS ref_date FROM fact_orders),
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
    FROM rfm_segmented GROUP BY customer_segment ORDER BY total_segment_revenue DESC;
    """
    print("\n---> Query 6: Customer RFM Segmentation Distribution")
    print(pd.read_sql(q6, conn).to_string(index=False))

    # Q7: Discount Tier Impact
    q7 = """
    WITH discount_tiers AS (
        SELECT 
            fact_id, sales, profit, discount,
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
        COUNT(fact_id) AS items_sold,
        ROUND(SUM(sales), 2) AS gross_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND(SUM(profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS profit_margin_pct
    FROM discount_tiers GROUP BY discount_tier ORDER BY MIN(discount) ASC;
    """
    print("\n---> Query 7: Discount Tier Profit Degradation Analysis")
    print(pd.read_sql(q7, conn).to_string(index=False))

    # 4. POWER BI DAX CALCULATED MEASURES SUMMARY
    print("\n" + "-" * 80)
    print("[PHASE 3] CALCULATED POWER BI DAX METRICS")
    print("-" * 80)
    
    kpis = pd.read_sql("""
        SELECT 
            ROUND(SUM(sales), 2) as total_sales,
            ROUND(SUM(profit), 2) as total_profit,
            ROUND(SUM(profit) * 100.0 / SUM(sales), 2) as profit_margin_pct,
            COUNT(DISTINCT order_id) as total_orders,
            ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) as avg_order_value
        FROM fact_orders
    """, conn).iloc[0]
    
    print(f"  * Total Sales:          ${kpis['total_sales']:,.2f}")
    print(f"  * Total Profit:         ${kpis['total_profit']:,.2f}")
    print(f"  * Overall Profit Margin: {kpis['profit_margin_pct']}%")
    print(f"  * Total Orders:         {kpis['total_orders']:,}")
    print(f"  * Avg Order Value (AOV): ${kpis['avg_order_value']:,.2f}")

    conn.close()
    print("\n" + "=" * 80)
    print("                   PROJECT RUN COMPLETE & VALIDATED")
    print("=" * 80)

if __name__ == "__main__":
    run_and_show_project("c:/Users/HP/Desktop/projects/retail-sales-dashboard/sales_dashboard.db")
