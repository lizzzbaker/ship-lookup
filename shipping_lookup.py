# shipping_lookup.py

import pandas as pd
import os
import sys
import re

# 1) Load SKU ↔ weight table
df = pd.read_csv('Item.csv', dtype={'SKU': str})
# normalize SKUs in the file
df['SKU'] = df['SKU'].str.strip().str.upper()
sku_to_weight = dict(zip(df['SKU'], df['Package Weight']))


# 2) Load weight brackets and shipping costs dynamically from shipping_schedule.csv
script_dir = os.path.dirname(os.path.abspath(__file__))
schedule_file = os.path.join(script_dir, 'shipping_schedule.csv')
try:
    sched_df = pd.read_csv(schedule_file)
except FileNotFoundError:
    print(f"ERROR: Could not find shipping schedule file at {schedule_file}", file=sys.stderr)
    sys.exit(1)

brackets = []
costs = []
labels = sched_df['Weight Bracket (lb)'].tolist()
for _, row in sched_df.iterrows():
    label = row['Weight Bracket (lb)']
    # parse numeric bounds
    if label.startswith('≤'):
        low = 0.0
        high = float(label.split()[1])
    else:
        parts = label.split('–')
        low = float(parts[0])
        high = float(parts[1].split()[0])
    brackets.append((low, high))
    # parse cost value
    cost_val = row['avg Shipping Charge']
    costs.append(float(str(cost_val).replace('$','')))

def get_shipping_cost(weight):
    """
    Return the shipping cost based on the item's weight in pounds.
    """
    for (low, high), cost in zip(brackets, costs):
        # Include the lower bound (except for the very first bracket)
        if (weight > low and weight <= high) or (low == 0 and weight <= 1):
            return cost
    return None

def lookup_sku(sku):
    """
    Lookup the estimated shipping cost for a given SKU.
    """
    weight = sku_to_weight.get(sku)
    if weight is None:
        return f"SKU '{sku}' not found in the weight table."
    cost = get_shipping_cost(weight)
    if cost is None:
        return f"Weight {weight} lb for SKU '{sku}' falls outside defined brackets."
    return f"Estimated shipping cost for SKU '{sku}' (weight {weight} lb): ${cost:.2f}"

if __name__ == "__main__":
    print("Shipping Cost Lookup")
    print("Type an SKU and press Enter. Type 'exit' to quit.\n")
    while True:
        sku_input = input("Enter SKU: ").strip()
        if sku_input.lower() == 'exit':
            print("Goodbye!")
            break
        print(lookup_sku(sku_input), "\n")