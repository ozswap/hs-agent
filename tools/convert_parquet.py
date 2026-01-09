#!/usr/bin/env python3
"""Convert Parquet files to CSV for use with benchmark_creator.html.

Usage:
    uv run python tools/convert_parquet.py /path/to/labels.parquet

This will create a CSV file in the same directory with the same name.
"""

import sys
from pathlib import Path

import pandas as pd


def convert_parquet_to_csv(parquet_path: Path) -> Path:
    """Convert a Parquet file to CSV."""
    df = pd.read_parquet(parquet_path)

    # Show info about the file
    print(f"Loaded {len(df)} rows with columns:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  - {col}: {non_null}/{len(df)} non-null")

    # Output path
    csv_path = parquet_path.with_suffix(".csv")

    # Save as CSV
    df.to_csv(csv_path, index=False)
    print(f"\nSaved to: {csv_path}")

    return csv_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python tools/convert_parquet.py <parquet_file>")
        sys.exit(1)

    parquet_path = Path(sys.argv[1])

    if not parquet_path.exists():
        print(f"Error: File not found: {parquet_path}")
        sys.exit(1)

    if parquet_path.suffix != ".parquet":
        print(f"Warning: File does not have .parquet extension: {parquet_path}")

    convert_parquet_to_csv(parquet_path)
