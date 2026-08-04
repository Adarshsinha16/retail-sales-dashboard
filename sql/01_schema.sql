-- ============================================================================
-- Phase 2: Relational Database Schema (Star Schema Design)
-- Database: PostgreSQL / SQLite Compatible
-- ============================================================================

-- Drop tables if exists (for clean execution)
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_regions;

-- 1. Dimension: Customers
CREATE TABLE dim_customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    segment VARCHAR(50) NOT NULL
);

-- 2. Dimension: Products
CREATE TABLE dim_products (
    product_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL
);

-- 3. Dimension: Regions & Locations
CREATE TABLE dim_regions (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_name VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'United States'
);

-- 4. Fact Table: Sales Orders
CREATE TABLE fact_orders (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE NOT NULL,
    ship_mode VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    region_id INTEGER NOT NULL,
    sales DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    discount DECIMAL(4, 2) NOT NULL,
    profit DECIMAL(10, 2) NOT NULL,
    order_processing_days INTEGER NOT NULL,
    profit_margin DECIMAL(6, 4) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (region_id) REFERENCES dim_regions(region_id)
);

-- Performance Indexes for Fast Query Execution
CREATE INDEX idx_fact_orders_order_date ON fact_orders(order_date);
CREATE INDEX idx_fact_orders_customer_id ON fact_orders(customer_id);
CREATE INDEX idx_fact_orders_product_id ON fact_orders(product_id);
CREATE INDEX idx_fact_orders_region_id ON fact_orders(region_id);
