import json

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Phase 1: Data Cleaning, Feature Engineering & Exploratory Data Analysis (EDA)\n",
    "## Retail Sales Performance Dashboard Portfolio Project\n",
    "\n",
    "### Objective\n",
    "In this phase, we load raw Kaggle Superstore Sales transactional data, audit data quality, fix data types, handle missing values, perform string standardization, engineer business-relevant derived columns, and analyze outliers."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "import os\n",
    "from sqlalchemy import create_engine\n",
    "\n",
    "# Set display options\n",
    "pd.set_option('display.max_columns', None)\n",
    "pd.set_option('display.float_format', lambda x: '%.2f' % x)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Load Raw Dataset & Baseline Audit\n",
    "We start by loading `superstore_sales.csv` and inspecting dataset dimensions, data types, null counts, and exact duplicates."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "raw_path = '../data/raw/superstore_sales.csv'\n",
    "df_raw = pd.read_csv(raw_path)\n",
    "print(f\"Dataset Shape: {df_raw.shape[0]} rows, {df_raw.shape[1]} columns\")\n",
    "df_raw.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Data Quality Findings\n",
    "- **Deduplication**: Found exact duplicate rows resulting from multi-line transaction logs.\n",
    "- **Date Parsing**: Date strings exist in mixed formats (`YYYY-MM-DD` and `MM/DD/YYYY`).\n",
    "- **Postal Code**: `Postal Code` imported as float with missing values (specifically for Burlington, NC)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Execute Data Cleaning\n",
    "import sys\n",
    "sys.path.append('..')\n",
    "from src.data_cleaning import clean_data\n",
    "df_cleaned = clean_data(df_raw)\n",
    "df_cleaned.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Decision Rationale & Defense Guide\n",
    "\n",
    "### Q1: Why Impute Postal Code instead of Dropping rows?\n",
    "**Defense**: Dropping rows with missing postal codes removes legitimate sales transactions and skews aggregate revenue and profit numbers. Imputing the known Burlington NC zip code (27215) or zero-padded string sentinel retains 100% of commercial revenue integrity.\n",
    "\n",
    "### Q2: Why Flag Outliers instead of Removing them?\n",
    "**Defense**: Retail transaction datasets contain legitimate high-volume enterprise orders and heavily discounted products resulting in severe negative margins. Removing outliers artificially deflates variance and creates false profit forecasts. Flagging them with `is_sales_outlier` allows filtering in Power BI without corrupting financial records.\n",
    "\n",
    "### Q3: Why store Postal Code as String rather than Integer?\n",
    "**Defense**: US Postal Codes (e.g. East Coast ZIP codes like Boston `02108`) start with leading zeros. Storing them as integers silently truncates `02108` into `2108`, breaking spatial joins and map visualizations in Power BI."
   ]
  }
 ],
 "metadata": {
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

with open("c:/Users/HP/Desktop/projects/retail-sales-dashboard/notebooks/01_data_cleaning_eda.ipynb", "w") as f:
    json.dump(notebook_content, f, indent=2)

print("Jupyter Notebook created at notebooks/01_data_cleaning_eda.ipynb")
