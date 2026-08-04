import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os

def load_and_inspect(file_path):
    """Load raw dataset and report baseline quality metrics."""
    print("=" * 60)
    print("STEP 1: RAW DATA INGESTION & INSPECTION")
    print("=" * 60)
    df = pd.read_csv(file_path)
    print(f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    print("\nColumn Data Types & Non-Null Counts:")
    print(df.info())
    print("\nMissing Values per Column:")
    print(df.isnull().sum()[df.isnull().sum() > 0])
    
    duplicate_count = df.duplicated().sum()
    print(f"\nExact Duplicate Rows Found: {duplicate_count}")
    return df

def clean_data(df):
    """Execute complete data cleaning, type conversion, and standardization."""
    print("\n" + "=" * 60)
    print("STEP 2: DATA CLEANING & TYPE CONVERSION")
    print("=" * 60)
    
    df_clean = df.copy()

    # 1. Deduplication
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    dropped_dupes = initial_rows - len(df_clean)
    print(f"[Deduplication] Removed {dropped_dupes} duplicate rows.")

    # 2. Datetime Conversion
    # Mixed formats handled robustly (e.g., YYYY-MM-DD and MM/DD/YYYY)
    df_clean['Order Date'] = pd.to_datetime(df_clean['Order Date'], format='mixed', errors='coerce')
    df_clean['Ship Date'] = pd.to_datetime(df_clean['Ship Date'], format='mixed', errors='coerce')
    print("[Type Fix] Converted 'Order Date' and 'Ship Date' to datetime64[ns].")

    # 3. Identifier & Postal Code Type Fix
    df_clean['Row ID'] = df_clean['Row ID'].astype(str)
    
    # Handle Missing Postal Codes: Burlington, NC is missing postal code in Superstore
    # Imputation Rationale: Drop vs Impute decision -> Impute known Burlington ZIP (27215)
    # or pad string to 5 digits so numeric lead-zeros (e.g. 02108 Boston) are preserved.
    df_clean['Postal Code'] = df_clean['Postal Code'].fillna('27215')
    df_clean['Postal Code'] = df_clean['Postal Code'].apply(lambda x: str(int(float(x))).zfill(5) if str(x).replace('.','').isdigit() else str(x))
    print("[Missing Value & Type Fix] Imputed missing 'Postal Code' and formatted as 5-digit string.")

    # 4. Categorical Standardization
    string_cols = ['Country', 'City', 'State', 'Region', 'Segment', 'Ship Mode', 'Category', 'Sub-Category']
    for col in string_cols:
        df_clean[col] = df_clean[col].astype(str).str.strip().str.title()
    print("[Standardization] Cleaned leading/trailing whitespace and standardized title casing for categorical columns.")

    # 5. Derived Feature Engineering
    print("\n" + "=" * 60)
    print("STEP 3: FEATURE ENGINEERING")
    print("=" * 60)
    
    # Processing duration in days
    df_clean['order_processing_days'] = (df_clean['Ship Date'] - df_clean['Order Date']).dt.days

    # Profit Margin % (Profit / Sales)
    # Prevent division by zero if sales == 0
    df_clean['profit_margin'] = np.where(
        df_clean['Sales'] > 0,
        np.round(df_clean['Profit'] / df_clean['Sales'], 4),
        0.0
    )

    # Date granularity features
    df_clean['order_year'] = df_clean['Order Date'].dt.year
    df_clean['order_month'] = df_clean['Order Date'].dt.month
    df_clean['order_quarter'] = df_clean['Order Date'].dt.quarter
    df_clean['year_month'] = df_clean['Order Date'].dt.strftime('%Y-%m')

    print("[Derived Features Created]:")
    print("  - order_processing_days (Ship Date - Order Date)")
    print("  - profit_margin (Profit / Sales)")
    print("  - order_year, order_month, order_quarter, year_month")

    # 6. Outlier Flagging (IQR Method)
    print("\n" + "=" * 60)
    print("STEP 4: OUTLIER ANALYSIS & FLAGGING")
    print("=" * 60)
    
    q1_sales = df_clean['Sales'].quantile(0.25)
    q3_sales = df_clean['Sales'].quantile(0.75)
    iqr_sales = q3_sales - q1_sales
    upper_sales = q3_sales + (1.5 * iqr_sales)

    q1_profit = df_clean['Profit'].quantile(0.25)
    q3_profit = df_clean['Profit'].quantile(0.75)
    iqr_profit = q3_profit - q1_profit
    lower_profit = q1_profit - (1.5 * iqr_profit)
    upper_profit = q3_profit + (1.5 * iqr_profit)

    df_clean['is_sales_outlier'] = df_clean['Sales'] > upper_sales
    df_clean['is_profit_outlier'] = (df_clean['Profit'] < lower_profit) | (df_clean['Profit'] > upper_profit)

    sales_outliers_count = df_clean['is_sales_outlier'].sum()
    profit_outliers_count = df_clean['is_profit_outlier'].sum()
    
    print(f"[Outlier Audit]:")
    print(f"  - Sales Outliers (> ${upper_sales:.2f}): {sales_outliers_count} rows ({sales_outliers_count/len(df_clean):.2%})")
    print(f"  - Profit Outliers (< ${lower_profit:.2f} or > ${upper_profit:.2f}): {profit_outliers_count} rows ({profit_outliers_count/len(df_clean):.2%})")
    print("  - Strategy Rationale: Outliers FLAGGED, NOT DELETED. High sales/loss transactions represent real commercial enterprise orders and heavy discount strategies!")

    return df_clean

def export_to_db_and_csv(df_clean, csv_path, db_path):
    """Export cleaned data to CSV and write into SQLite relational database."""
    print("\n" + "=" * 60)
    print("STEP 5: DATA EXPORT & DATABASE INGESTION")
    print("=" * 60)
    
    # Save Cleaned CSV
    df_clean.to_csv(csv_path, index=False)
    print(f"[CSV Saved]: Cleaned data written to {csv_path}")

    # SQL Ingestion via SQLAlchemy
    engine = create_engine(f'sqlite:///{db_path}')
    df_clean.to_sql('raw_flat_orders', engine, if_exists='replace', index=False)
    print(f"[Database Ingested]: Written to SQLite database table 'raw_flat_orders' at {db_path}")

if __name__ == "__main__":
    raw_path = "c:/Users/HP/Desktop/projects/retail-sales-dashboard/data/raw/superstore_sales.csv"
    cleaned_csv_path = "c:/Users/HP/Desktop/projects/retail-sales-dashboard/data/cleaned/superstore_cleaned.csv"
    db_path = "c:/Users/HP/Desktop/projects/retail-sales-dashboard/sales_dashboard.db"

    df_raw = load_and_inspect(raw_path)
    df_cleaned = clean_data(df_raw)
    export_to_db_and_csv(df_cleaned, cleaned_csv_path, db_path)
    print("\n[SUCCESS] Phase 1 Data Cleaning & Feature Engineering Complete!")
