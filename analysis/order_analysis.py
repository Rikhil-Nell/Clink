# %%
# 📦 STEP 1: Load Libraries
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations
from collections import Counter

# Display settings
pd.set_option('display.max_columns', None)
sns.set_theme(style="whitegrid")

# %%
# 📂 STEP 2: Load Data
df = pd.read_csv("Year Order Item Data.csv", parse_dates=['date'])

# Quick glance at data
df.head()

# %%
# 🧹 STEP 3: Clean Data Types & Handle Missing
numeric_cols = [
    'my_amount', 'total_tax', 'discount', 'delivery_charge',
    'container_charge', 'service_charge', 'additional_charge',
    'waived_off', 'round_off', 'total', 'item_price', 'item_quantity', 'item_total'
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Fill common missing numeric fields with 0
df[['discount', 'waived_off']] = df[['discount', 'waived_off']].fillna(0)

# Drop records missing critical order-level info
df.dropna(subset=['invoice_no', 'item_name', 'item_quantity', 'item_total'], inplace=True)

# Recompute net sales at line level
df['net_sales'] = df['item_total'] - df[['discount', 'waived_off']].sum(axis=1)

# Time-based features
df['YearMonth'] = df['date'].dt.to_period('M')
df['DateOnly'] = df['date'].dt.date
df['Weekday'] = df['date'].dt.day_name()
df['Hour'] = df['date'].dt.hour

df.info()

# %%
# 🧮 STEP 4: Invoice-Level KPI Aggregation

invoice_kpis = (
    df.groupby('invoice_no').agg(
        order_date=('date', 'min'),
        customer_phone=('customer_phone', 'first'),
        customer_name=('customer_name', 'first'),
        total_items=('item_name', 'nunique'),
        total_quantity=('item_quantity', 'sum'),
        total_discount=('discount', 'sum'),
        total_waived_off=('waived_off', 'sum'),
        net_invoice_value=('net_sales', 'sum')
    ).reset_index()
)

# Add easy date breakdowns
invoice_kpis['order_day'] = invoice_kpis['order_date'].dt.day_name()
invoice_kpis['order_date_only'] = invoice_kpis['order_date'].dt.date

invoice_kpis.head()

# %%
# 💾 Save for future use
invoice_kpis.to_csv("../results/order_analysis/Invoice_Aggregation.csv", index=False)

# %%
# 🤝 STEP 5: Build Product Co-Occurrence
# Group items by invoice
invoice_items = df.groupby('invoice_no')['item_name'].apply(list).reset_index()

# Check basic basket stats
invoice_items['basket_size'] = invoice_items['item_name'].apply(lambda x: len(set(x)))
invoice_items['basket_size'].describe()

# %%
# Function to build pair counts
def build_pair_counter(item_lists):
    pair_counter = Counter()
    for items in item_lists:
        unique_items = list(set(items))
        if len(unique_items) > 1:
            pairs = combinations(sorted(unique_items), 2)
            pair_counter.update(pairs)
    return pair_counter

# Build pair counts
pair_counter = build_pair_counter(invoice_items['item_name'])
pair_counter.most_common(10)

# %%
# Convert to dataframe for analysis
co_occurrence_df = pd.DataFrame(pair_counter.items(), columns=['item_pair', 'count'])
co_occurrence_df[['item_1', 'item_2']] = pd.DataFrame(co_occurrence_df['item_pair'].tolist(), index=co_occurrence_df.index)
co_occurrence_df.drop(columns='item_pair', inplace=True)
co_occurrence_df.sort_values(by='count', ascending=False, inplace=True)

co_occurrence_df.head()

# %%
# 🔥 STEP 6: Symmetric Co-Occurrence Matrix

matrix_df = pd.pivot_table(
    co_occurrence_df,
    values='count',
    index='item_1',
    columns='item_2',
    fill_value=0
)

# Make it symmetric
full_matrix = matrix_df + matrix_df.T.fillna(0)

full_matrix.head()

# %%
# 🌡️ STEP 7: Heatmap for ALL Co-Occurrences

plt.figure(figsize=(18, 14))
sns.heatmap(full_matrix, cmap='YlGnBu', linewidths=0.5, linecolor='gray')

plt.title("Product Co-Occurrence Heatmap (Full Matrix)", fontsize=18)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# %%
# 🎯 STEP 8: Filtered Heatmap for Top-N frequent items
top_items = df['item_name'].value_counts().head(30).index
filtered_matrix = full_matrix.loc[top_items, top_items]

plt.figure(figsize=(16, 12))
sns.heatmap(filtered_matrix, cmap='YlGnBu', linewidths=0.5, linecolor='gray')

plt.title("Product Co-Occurrence Heatmap (Top 30 Items)", fontsize=16)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# %%
# 💾 Save matrices
# full_matrix.to_csv("../results/order_analysis/Product_Co_occurrence_Full.csv")
filtered_matrix.to_csv("../results/order_analysis/Product_Co_occurrence_Top30.csv")

# %%
# 🏋️ STEP 9: Compute Lift Metrics (with support filtering)

min_item_support = 20  # each item must appear in at least 20 invoices
min_pair_support = 5   # each pair must co-occur in at least 5 invoices

# Number of unique invoices
total_invoices = df['invoice_no'].nunique()

# Frequency (support) of each individual item
item_invoice_counts = df.groupby('item_name')['invoice_no'].nunique()
item_invoice_support = item_invoice_counts / total_invoices

# Filter items by minimum support
frequent_items = item_invoice_counts[item_invoice_counts >= min_item_support].index.tolist()

print(f"Found {len(frequent_items)} items with at least {min_item_support} invoices.")

filtered_pairs_df = co_occurrence_df[
    co_occurrence_df['item_1'].isin(frequent_items) &
    co_occurrence_df['item_2'].isin(frequent_items) &
    (co_occurrence_df['count'] >= min_pair_support)
].copy()

print(f"Reduced to {filtered_pairs_df.shape[0]} item pairs after filtering.")

def compute_lift(row):
    A, B = row['item_1'], row['item_2']
    pair_support = row['count'] / total_invoices
    expected_support = item_invoice_support[A] * item_invoice_support[B]
    if expected_support > 0:
        return pair_support / expected_support
    else:
        return np.nan

filtered_pairs_df['lift'] = filtered_pairs_df.apply(compute_lift, axis=1)

# Sort by lift descending
filtered_pairs_df.sort_values(by='lift', ascending=False, inplace=True)

filtered_pairs_df.head(15)

filtered_pairs_df.to_csv("../results/order_analysis/Item_Pair_Lift_Analysis.csv", index=False)



