import sqlite3
import pandas as pd

def populate_star_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Executing DDL to create Star Schema tables...")
    
    # 1. Create Tables
    cursor.executescript("""
    DROP TABLE IF EXISTS fact_orders;
    DROP TABLE IF EXISTS dim_customers;
    DROP TABLE IF EXISTS dim_products;
    DROP TABLE IF EXISTS dim_regions;

    CREATE TABLE dim_customers (
        customer_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        segment TEXT NOT NULL
    );

    CREATE TABLE dim_products (
        product_id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        sub_category TEXT NOT NULL,
        product_name TEXT NOT NULL
    );

    CREATE TABLE dim_regions (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL,
        state TEXT NOT NULL,
        city TEXT NOT NULL,
        postal_code TEXT NOT NULL,
        country TEXT NOT NULL DEFAULT 'United States'
    );

    CREATE TABLE fact_orders (
        fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        row_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        order_date TEXT NOT NULL,
        ship_date TEXT NOT NULL,
        ship_mode TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        region_id INTEGER NOT NULL,
        sales REAL NOT NULL,
        quantity INTEGER NOT NULL,
        discount REAL NOT NULL,
        profit REAL NOT NULL,
        order_processing_days INTEGER NOT NULL,
        profit_margin REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
        FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
        FOREIGN KEY (region_id) REFERENCES dim_regions(region_id)
    );
    """)
    conn.commit()

    # Load cleaned flat table
    df = pd.read_sql("SELECT * FROM raw_flat_orders", conn)
    print(f"Loaded {len(df)} records from raw_flat_orders.")

    # Populate dim_customers
    dim_cust = df[['Customer ID', 'Customer Name', 'Segment']].drop_duplicates(subset=['Customer ID'])
    dim_cust.columns = ['customer_id', 'customer_name', 'segment']
    dim_cust.to_sql('dim_customers', conn, if_exists='append', index=False)
    print(f"Populated dim_customers: {len(dim_cust)} rows.")

    # Populate dim_products
    dim_prod = df[['Product ID', 'Category', 'Sub-Category', 'Product Name']].drop_duplicates(subset=['Product ID'])
    dim_prod.columns = ['product_id', 'category', 'sub_category', 'product_name']
    dim_prod.to_sql('dim_products', conn, if_exists='append', index=False)
    print(f"Populated dim_products: {len(dim_prod)} rows.")

    # Populate dim_regions
    dim_reg = df[['Region', 'State', 'City', 'Postal Code', 'Country']].drop_duplicates(
        subset=['Region', 'State', 'City', 'Postal Code']
    ).reset_index(drop=True)
    dim_reg.columns = ['region_name', 'state', 'city', 'postal_code', 'country']
    dim_reg.to_sql('dim_regions', conn, if_exists='append', index=False)
    print(f"Populated dim_regions: {len(dim_reg)} rows.")

    # Read back dim_regions with auto-generated region_id
    df_regions_db = pd.read_sql("SELECT region_id, region_name, state, city, postal_code FROM dim_regions", conn)

    # Merge region_id into main orders dataframe
    df_merged = df.merge(
        df_regions_db,
        left_on=['Region', 'State', 'City', 'Postal Code'],
        right_on=['region_name', 'state', 'city', 'postal_code'],
        how='left'
    )

    # Prepare fact_orders dataframe
    fact_orders_df = df_merged[[
        'Row ID', 'Order ID', 'Order Date', 'Ship Date', 'Ship Mode',
        'Customer ID', 'Product ID', 'region_id',
        'Sales', 'Quantity', 'Discount', 'Profit',
        'order_processing_days', 'profit_margin'
    ]].copy()

    fact_orders_df.columns = [
        'row_id', 'order_id', 'order_date', 'ship_date', 'ship_mode',
        'customer_id', 'product_id', 'region_id',
        'sales', 'quantity', 'discount', 'profit',
        'order_processing_days', 'profit_margin'
    ]

    fact_orders_df.to_sql('fact_orders', conn, if_exists='append', index=False)
    print(f"Populated fact_orders: {len(fact_orders_df)} rows.")

    # Build Performance Indexes
    cursor.executescript("""
    CREATE INDEX idx_fact_orders_order_date ON fact_orders(order_date);
    CREATE INDEX idx_fact_orders_customer_id ON fact_orders(customer_id);
    CREATE INDEX idx_fact_orders_product_id ON fact_orders(product_id);
    CREATE INDEX idx_fact_orders_region_id ON fact_orders(region_id);
    """)
    conn.commit()
    conn.close()
    print("Database Star Schema Population Complete!")

if __name__ == "__main__":
    populate_star_schema("c:/Users/HP/Desktop/projects/retail-sales-dashboard/sales_dashboard.db")
