import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_superstore_dataset(num_rows=9994):
    np.random.seed(42)
    random.seed(42)

    categories = {
        'Furniture': ['Bookcases', 'Chairs', 'Tables', 'Furnishings'],
        'Office Supplies': ['Labels', 'Storage', 'Art', 'Binders', 'Appliances', 'Paper', 'Envelopes', 'Fasteners', 'Supplies'],
        'Technology': ['Phones', 'Accessories', 'Machines', 'Copiers']
    }
    
    regions_states = {
        'West': [('California', 'Los Angeles', 90036), ('Washington', 'Seattle', 98109), ('Arizona', 'Phoenix', 85001), ('Oregon', 'Portland', 97201)],
        'East': [('New York', 'New York City', 10024), ('Pennsylvania', 'Philadelphia', 19104), ('Ohio', 'Columbus', 43215), ('Massachusetts', 'Boston', 2108)],
        'Central': [('Illinois', 'Chicago', 60611), ('Texas', 'Houston', 77002), ('Michigan', 'Detroit', 48201), ('Wisconsin', 'Milwaukee', 53202)],
        'South': [('Florida', 'Miami', 33133), ('North Carolina', 'Burlington', None), ('Virginia', 'Richmond', 23219), ('Georgia', 'Atlanta', 30301)]
    }

    segments = ['Consumer', 'Corporate', 'Home Office']
    ship_modes = ['Standard Class', 'Second Class', 'First Class', 'Same Day']

    # Generate Customers
    customers = []
    first_names = ['Claire', 'Ryan', 'Sarah', 'Michael', 'Emily', 'David', 'Jessica', 'James', 'Amanda', 'John', 'Laura', 'Robert', 'Ashley', 'William', 'Megan']
    last_names = ['Gute', 'Powers', 'Foster', 'Smith', 'Johnson', 'Miller', 'Davis', 'Wilson', 'Anderson', 'Taylor', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin']
    
    for i in range(793): # Standard Superstore has ~793 distinct customers
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        c_id = f"{fn[0]}{ln[0]}-{random.randint(10000, 99999)}"
        c_name = f"{fn} {ln}"
        seg = random.choice(segments)
        customers.append((c_id, c_name, seg))

    # Generate Products
    products = []
    prod_counter = 1
    for cat, subcats in categories.items():
        cat_prefix = cat[:3].upper()
        for subcat in subcats:
            sub_prefix = subcat[:2].upper()
            for _ in range(random.randint(15, 35)):
                p_id = f"{cat_prefix}-{sub_prefix}-{10000000 + prod_counter}"
                p_name = f"{subcat} Model {random.choice(['Pro', 'Plus', 'Ultra', 'Standard', 'Lite'])} {random.randint(100, 999)}"
                base_price = round(random.uniform(10, 500), 2)
                if subcat in ['Copiers', 'Machines', 'Tables']:
                    base_price = round(random.uniform(400, 3000), 2)
                products.append((p_id, cat, subcat, p_name, base_price))
                prod_counter += 1

    start_date = datetime(2021, 1, 1)
    
    rows = []
    order_seq = 100000

    for i in range(1, num_rows + 1):
        if i % 3 == 0 and rows:
            # Re-use order ID for multi-item orders
            prev_row = rows[-1]
            order_id = prev_row['Order ID']
            order_date = prev_row['Order Date']
            ship_date = prev_row['Ship Date']
            ship_mode = prev_row['Ship Mode']
            c_id, c_name, seg = prev_row['Customer ID'], prev_row['Customer Name'], prev_row['Segment']
            region = prev_row['Region']
            state = prev_row['State']
            city = prev_row['City']
            postal_code = prev_row['Postal Code']
        else:
            order_seq += 1
            region = random.choice(list(regions_states.keys()))
            state, city, postal_code = random.choice(regions_states[region])
            order_id = f"CA-{random.randint(2021, 2024)}-{order_seq}"
            days_offset = random.randint(0, 1400)
            order_dt = start_date + timedelta(days=days_offset)
            order_date = order_dt.strftime('%Y-%m-%d')
            
            ship_days = random.choices([1, 2, 4, 6], weights=[10, 20, 50, 20])[0]
            ship_dt = order_dt + timedelta(days=ship_days)
            ship_date = ship_dt.strftime('%Y-%m-%d')
            ship_mode = random.choice(ship_modes)
            c_id, c_name, seg = random.choice(customers)

        prod = random.choice(products)
        p_id, cat, subcat, p_name, base_price = prod
        
        qty = random.randint(1, 9)
        discount = random.choice([0.0, 0.0, 0.0, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 0.8])
        
        # Calculate sales & profit (high discounts create negative profit)
        unit_sales = base_price * (1 - discount)
        sales = round(unit_sales * qty, 2)
        
        cost = base_price * 0.6 * qty
        profit = round(sales - cost, 2)

        # Introduce realistic raw data noise / dirty data
        # 1. Dirty Casing in Region
        if random.random() < 0.05:
            region_str = region.lower() if random.random() < 0.5 else f" {region} "
        else:
            region_str = region

        # 2. Date format variations (some MM/DD/YYYY, some YYYY-MM-DD)
        if random.random() < 0.08:
            order_date_str = order_dt.strftime('%m/%d/%Y')
        else:
            order_date_str = order_date

        rows.append({
            'Row ID': i,
            'Order ID': order_id,
            'Order Date': order_date_str,
            'Ship Date': ship_date,
            'Ship Mode': ship_mode,
            'Customer ID': c_id,
            'Customer Name': c_name,
            'Segment': seg,
            'Country': 'United States',
            'City': city,
            'State': state,
            'Postal Code': postal_code,
            'Region': region_str,
            'Product ID': p_id,
            'Category': cat,
            'Sub-Category': subcat,
            'Product Name': p_name,
            'Sales': sales,
            'Quantity': qty,
            'Discount': discount,
            'Profit': profit
        })

    df = pd.DataFrame(rows)

    # Add intentional duplicate rows (e.g. 5 exact duplicates)
    dupes = df.sample(5, random_state=42)
    df = pd.concat([df, dupes], ignore_index=True)

    # Inject extreme high sales outlier (e.g. enterprise bulk transaction)
    df.loc[100, 'Sales'] = 22638.48
    df.loc[100, 'Profit'] = 8399.98

    # Inject loss outlier
    df.loc[250, 'Sales'] = 4499.98
    df.loc[250, 'Profit'] = -6599.98

    return df

if __name__ == "__main__":
    df_raw = generate_superstore_dataset(9994)
    target_path = "c:/Users/HP/Desktop/projects/retail-sales-dashboard/data/raw/superstore_sales.csv"
    df_raw.to_csv(target_path, index=False)
    print(f"Raw Superstore dataset generated successfully at: {target_path}")
    print(f"Dataset Shape: {df_raw.shape}")
