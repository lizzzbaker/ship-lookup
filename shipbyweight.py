#!/usr/bin/env python3
import pandas as pd
import argparse
import glob
import os
import sys

# Ensure the script's directory is on the import path so shipping_lookup can be found
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import weight bracket definitions from shipping_lookup.py
try:
    from shipping_lookup import brackets as WEIGHT_BRACKETS, labels as BRACKET_LABELS
except ImportError:
    print("ERROR: Could not import weight bracket definitions from shipping_lookup.py", file=sys.stderr)
    sys.exit(1)


def load_data(patterns, weight_col, cost_col, unit):
    dfs = []
    for pat in patterns:
        for path in glob.glob(pat):
            if not os.path.isfile(path):
                continue
            df = pd.read_csv(path)
            # Ensure required columns exist
            if weight_col not in df.columns or cost_col not in df.columns:
                print(f"ERROR: Missing columns in {path}", file=sys.stderr)
                sys.exit(1)
            df = df[[weight_col, cost_col]].copy()
            # Convert weight to pounds if unit is ounces
            if unit == 'oz':
                df['weight_lb'] = df[weight_col] / 16.0
            else:
                df['weight_lb'] = df[weight_col]
            dfs.append(df[['weight_lb', cost_col]])
    if not dfs:
        print("ERROR: No input files found", file=sys.stderr)
        sys.exit(1)
    return pd.concat(dfs, ignore_index=True)


def main():
    parser = argparse.ArgumentParser(description="Update shipping schedule.")
    parser.add_argument('-i', '--input', nargs='+', required=True,
                        help="CSV files or glob patterns with weight and cost.")
    parser.add_argument('-o', '--output', default='shipping_schedule.csv',
                        help="Output CSV path.")
    parser.add_argument('--weight-col', default='variant_weight',
                        help="Weight column name (default: variant_weight).")
    parser.add_argument('--cost-col', default='delivery_cost',
                        help="Cost column name (default: delivery_cost).")
    parser.add_argument('--unit', choices=['oz','lb'], default='oz',
                        help="Unit of weight column (default: oz).")
    args = parser.parse_args()

    # Load and preprocess data
    df = load_data(args.input, args.weight_col, args.cost_col, args.unit)

    # Build bin edges from imported WEIGHT_BRACKETS
    edges = [low for low, _ in WEIGHT_BRACKETS] + [WEIGHT_BRACKETS[-1][1]]
    df['Weight Bracket (lb)'] = pd.cut(
        df['weight_lb'],
        bins=edges,
        labels=BRACKET_LABELS,
        include_lowest=True
    )

    # Compute average shipping cost per bracket
    summary = (
        df
        .groupby('Weight Bracket (lb)')[args.cost_col]
        .mean()
        .round(2)
        .reset_index()
    )

    # Format as currency string
    summary['avg Shipping Charge'] = summary[args.cost_col].apply(lambda x: f"${x:.2f}")

    # Ensure all brackets are present
    result = (
        pd.DataFrame({'Weight Bracket (lb)': BRACKET_LABELS})
        .merge(
            summary[['Weight Bracket (lb)', 'avg Shipping Charge']],
            on='Weight Bracket (lb)', how='left'
        )
    )

    # Write to output
    result.to_csv(args.output, index=False)
    print(f"Written to {args.output}")

if __name__ == "__main__":
    main()
