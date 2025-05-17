#!/usr/bin/env python3
import pandas as pd
import argparse, glob, os, sys

# Import weight brackets from your lookup definitions
try:
    from shipping_lookup import brackets as BINS, labels as LABELS
except ImportError:
    print("ERROR: shipping_lookup.py not found.", file=sys.stderr)
    sys.exit(1)

def load_data(patterns, weight_col, cost_col, unit):
    dfs = []
    for pat in patterns:
        for path in glob.glob(pat):
            df = pd.read_csv(path)
            if weight_col not in df or cost_col not in df:
                print(f"ERROR: Missing columns in {path}", file=sys.stderr)
                sys.exit(1)
            sub = df[[weight_col, cost_col]].copy()
            sub['weight_lb'] = sub[weight_col]/16 if unit=='oz' else sub[weight_col]
            dfs.append(sub)
    if not dfs:
        print("ERROR: No input files found.", file=sys.stderr)
        sys.exit(1)
    return pd.concat(dfs, ignore_index=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i','--input',nargs='+', required=True,
                   help="CSV files or glob of orders with weight_lb & delivery_cost")
    p.add_argument('-o','--output', default='shipping_schedule.csv')
    p.add_argument('--weight-col', default='weight_lb')
    p.add_argument('--cost-col', default='delivery_cost')
    p.add_argument('--unit', choices=['oz','lb'], default='oz')
    args = p.parse_args()

    df = load_data(args.input, args.weight_col, args.cost_col, args.unit)
    df['Weight Bracket (lb)'] = pd.cut(df['weight_lb'], bins=BINS, labels=LABELS, include_lowest=True)
    summary = ( df.groupby('Weight Bracket (lb)')[args.cost_col]
                 .mean().round(2).reset_index() )
    summary['avg Shipping Charge'] = summary[args.cost_col].map(lambda x: f"${x:.2f}")
    # ensure all brackets present
    out = pd.DataFrame({'Weight Bracket (lb)': LABELS}) \
            .merge(summary[['Weight Bracket (lb)','avg Shipping Charge']],
                   on='Weight Bracket (lb)', how='left')
    out.to_csv(args.output, index=False)
    print(f"Written {args.output}")

if __name__=='__main__':
    main()