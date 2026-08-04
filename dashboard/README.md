# Power BI Dashboard Setup & Visual Architecture Guide

This directory contains the DAX measures reference and visual configuration blueprint for building the **Retail Sales Performance Dashboard** in Power BI Desktop (.pbix).

---

## 1. Database Connection & Data Model Architecture

### Database Connection Steps:
1. Open **Power BI Desktop**.
2. Click **Get Data** → Select **SQLite Database** (or **ODBC** / **PostgreSQL Database**).
3. Connect to `sales_dashboard.db` or PostgreSQL server.
4. Import four tables: `fact_orders`, `dim_customers`, `dim_products`, `dim_regions`.

### Date Table Creation (DAX):
Navigate to **Modeling** → **New Table** and paste:
```dax
Dim_Date = 
VAR MinYear = YEAR(MIN(fact_orders[order_date]))
VAR MaxYear = YEAR(MAX(fact_orders[order_date]))
RETURN
ADDCOLUMNS(
    CALENDAR(DATE(MinYear, 1, 1), DATE(MaxYear, 12, 31)),
    "Year", YEAR([Date]),
    "Quarter", "Q" & FORMAT([Date], "Q"),
    "YearQuarter", YEAR([Date]) & "-Q" & FORMAT([Date], "Q"),
    "MonthNo", MONTH([Date]),
    "MonthName", FORMAT([Date], "MMM"),
    "YearMonth", FORMAT([Date], "YYYY-MM"),
    "DayOfWeek", FORMAT([Date], "ddd"),
    "DayNo", DAY([Date])
)
```

### Star Schema Relationships:
- `Dim_Date[Date]` `1` <---> `*` `fact_orders[order_date]` (Active)
- `dim_customers[customer_id]` `1` <---> `*` `fact_orders[customer_id]` (Active)
- `dim_products[product_id]` `1` <---> `*` `fact_orders[product_id]` (Active)
- `dim_regions[region_id]` `1` <---> `*` `fact_orders[region_id]` (Active)

---

## 2. Page-by-Page Visual Architecture

### Page 1: Executive Overview
* **Header / Top Slicers**:
  - Date Range Slicer (`Dim_Date[Date]` Slider)
  - Region Slicer (`dim_regions[region_name]` Dropdown)
  - Category Slicer (`dim_products[category]` Pills)
* **KPI Cards (Top Banner)**:
  - Card 1: `[Total Sales]` (Formatted as $ Millions)
  - Card 2: `[Total Profit]` (Formatted as $ Thousands)
  - Card 3: `[Profit Margin %]` (Formatted as %)
  - Card 4: `[Total Orders]` (Formatted as Integer)
  - Card 5: `[Avg Order Value (AOV)]` (Formatted as $)
* **Main Visuals**:
  1. **Revenue & Profit Monthly Trend (Combo Chart)**:
     - X-Axis: `Dim_Date[YearMonth]`
     - Column Y-Axis: `[Total Sales]`
     - Line Y-Axis: `[Profit Margin %]`
  2. **Regional Revenue Distribution (Filled Map / Shape Map)**:
     - Location: `dim_regions[state]`
     - Color Saturation: `[Total Sales]`
     - Tooltips: `[Total Profit]`, `[Profit Margin %]`
  3. **Sales by Customer Segment (Donut Chart)**:
     - Legend: `dim_customers[segment]`
     - Values: `[Total Sales]`

---

### Page 2: Category & Product Deep Dive
* **Main Visuals**:
  1. **Category & Sub-Category Performance (Matrix Visual)**:
     - Rows: `dim_products[category]` → `dim_products[sub_category]`
     - Columns / Values: `[Total Sales]`, `[Total Profit]`, `[Profit Margin %]`, `[Average Discount %]`
     - Conditional Formatting: Background color gradient on `[Profit Margin %]` (Red for negative, Green for positive).
  2. **Top 10 Loss-Making Products (Clustered Bar Chart)**:
     - Y-Axis: `dim_products[product_name]`
     - X-Axis: `[Total Profit]` (Filtered to `[Total Profit] < 0`)
     - Tooltip: `[Average Discount %]`
  3. **Discount vs Profit Margin Scatter Plot**:
     - X-Axis: `[Average Discount %]`
     - Y-Axis: `[Profit Margin %]`
     - Size: `[Total Sales]`
     - Details: `dim_products[sub_category]`
     - Analytical Trend Line: Linear regression line illustrating profit degradation above 20% discount.

---

### Page 3: Customer Intelligence & RFM Analysis
* **Main Visuals**:
  1. **RFM Customer Segment Distribution (Treemap / Bar Chart)**:
     - Group: Customer RFM Segment (`Champions`, `Loyal Customers`, `At Risk`, `Lost Customers`)
     - Values: `[Total Sales]`
  2. **Regional Churn Rate % (Clustered Column Chart)**:
     - X-Axis: `dim_regions[region_name]`
     - Y-Axis: `[Churn Rate %]`
  3. **Top 10 Customer LTV Table**:
     - Columns: `dim_customers[customer_name]`, `dim_customers[segment]`, `[Total Orders]`, `[Total Sales]`, `[Total Profit]`, `[Days Since Last Purchase]`
     - Sort: Descending by `[Total Sales]`

---

## 3. DAX Formulas Summary Reference

Refer to [dax_measures.dax](file:///c:/Users/HP/Desktop/projects/retail-sales-dashboard/dashboard/dax_measures.dax) for the full code file containing all formulas:
- Baseline: `[Total Sales]`, `[Total Profit]`, `[Profit Margin %]`, `[AOV]`
- Time Intelligence: `[YoY Sales Growth %]`, `[Running Total Sales (YTD)]`, `[Sales PY]`
- Customer Metrics: `[Active Customers]`, `[Churned Customers Count]`, `[Churn Rate %]`, `[Avg Customer LTV]`
- Pricing Sensitivity: `[High Discount Sales (>40%)]`, `[High Discount Loss]`
