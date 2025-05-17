#!/usr/bin/env python3
"""
shipping_data.py

Generates a static JSON mapping of SKU → shipping cost, based on:
  - Item.csv          (SKU, Package Weight)
  - shipping_schedule.csv  (Weight Bracket, avg Shipping Charge)

Outputs:
  sku_to_cost.json
"""
import pandas as pd
import json
import os
import sys

# Constants
ITEM_FILE = 'Item.csv'
SCHEDULE_FILE = 'shipping_schedule.csv'
OUTPUT_JSON = 'sku_to_cost.json'

# Verify inputs
for path in (ITEM_FILE, SCHEDULE_FILE):
    if not os.path.isfile(path):
        print(f"ERROR: Required file not found: {path}", file=sys.stderr)
        sys.exit(1)

# 1) Load item weights
df_items = pd.read_csv(ITEM_FILE, dtype={'SKU': str})
# Normalize SKU column
if 'SKU' not in df_items.columns or 'Package Weight' not in df_items.columns:
    print(f"ERROR: {ITEM_FILE} must contain 'SKU' and 'Package Weight' columns", file=sys.stderr)
    sys.exit(1)
df_items['SKU'] = df_items['SKU'].astype(str).str.strip().str.upper()

# 2) Load shipping schedule
sched_df = pd.read_csv(SCHEDULE_FILE)
if 'Weight Bracket (lb)' not in sched_df.columns or 'avg Shipping Charge' not in sched_df.columns:
    print(f"ERROR: {SCHEDULE_FILE} must contain 'Weight Bracket (lb)' and 'avg Shipping Charge' columns", file=sys.stderr)
    sys.exit(1)

# Parse brackets and costs
brackets = []  # list of (low, high)
costs = []     # corresponding cost
labels = sched_df['Weight Bracket (lb)'].tolist()
for label, cost_str in zip(sched_df['Weight Bracket (lb)'], sched_df['avg Shipping Charge']):
    # cost
    cost = float(str(cost_str).replace('$',''))
    costs.append(cost)
    # bounds
    if isinstance(label, str) and label.startswith('≤'):
        # format '≤ 1 lb'
        parts = label.split()
        high = float(parts[1])
        low = 0.0
    else:
        # format '6–10 lb' or '3–6 lb'
        parts = label.split('–')
        low = float(parts[0])
        high = float(parts[1].split()[0])
    brackets.append((low, high))

# 3) Build mapping SKU -> cost
mapping = {}
for _, row in df_items.iterrows():
    sku = row['SKU']
    wt = float(row['Package Weight'])
    # find bracket
    cost_val = None
    for (low, high), cost in zip(brackets, costs):
        if (low == 0 and wt <= high) or (wt > low and wt <= high):
            cost_val = cost
            break
    mapping[sku] = cost_val

# 4) Write JSON
with open(OUTPUT_JSON, 'w') as f:
    json.dump(mapping, f, indent=2)

print(f"Generated {OUTPUT_JSON} with {len(mapping)} entries.")
