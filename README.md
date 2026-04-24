# Kmeans - Dataset Generator

Synthetic dataset generator for marketplace-order clustering experiments.

## What it generates

The main script produces a flat CSV where each row represents a synthetic marketplace order with fields such as:

- customer and seller identifiers
- location and delivery distance
- basket composition by category
- order totals, discounts, taxes, and marketplace fees
- payment, fulfillment, return, and delivery signals

The helper scripts still work the same way:

- `just generate` creates `data/orders.csv` with 1000 rows by default
- `just generate <size>` creates `data/orders.csv` with a custom number of rows
- `just bound` computes `data/mins_and_maxs.csv`
- `just feature` extracts `data/features.csv`

## Usage

```bash
just generate
just generate 5750000
just bound
just feature
```

> To generate a larger dataset with approx. 1GB, you should generate 5750000 lines
