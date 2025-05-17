#!/usr/bin/env bash
set -e

# 1) If there are any order CSVs in data/, regenerate the shipping schedule
if compgen -G "data/*.csv" > /dev/null; then
    echo "Found input CSVs in data/, updating shipping_schedule.csv..."
    python update_shipping_schedule.py \
        -i data/*.csv \
        -o shipping_schedule.csv
else
    echo "No input CSVs found in data/, skipping update step"
fi

# 2) Regenerate the static JSON lookup (if you have shipping_data.py)
if [ -f shipping_data.py ]; then
    echo "Generating sku_to_cost.json..."
    python shipping_data.py
else
    echo "shipping_data.py not found; skipping JSON generation"
fi

echo "✅ All steps completed."