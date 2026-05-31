"""
data_profiler.py
----------------
Automatic dataset understanding engine.
Profiles columns, detects types, summarizes quality, and extracts statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


# ── Column Type Detection ──────────────────────────────────────────────────

def detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Classifies each column into a semantic type:
      - 'numeric'      → integers or floats
      - 'categorical'  → low-cardinality text/object columns
      - 'datetime'     → date/time columns
      - 'text'         → high-cardinality string columns (e.g. comments, names)
      - 'boolean'      → True/False columns

    WHY: Pandas dtypes alone aren't enough. A column of "0/1" integers might be
    boolean; a column of 500 unique strings is free text, not a category.
    We layer semantic meaning on top of raw dtypes.
    """
    col_types = {}

    for col in df.columns:
        series = df[col].dropna()

        if series.empty:
            col_types[col] = "empty"
            continue

        dtype = df[col].dtype

        # Boolean check first (before numeric, since bool is a subtype of int)
        if dtype == bool or set(series.unique()).issubset({0, 1, True, False}):
            col_types[col] = "boolean"

        # Numeric
        elif pd.api.types.is_numeric_dtype(dtype):
            col_types[col] = "numeric"

        # Datetime
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            col_types[col] = "datetime"

        # Object / string columns — decide categorical vs text
        elif dtype == object:
            # Try parsing as datetime
            try:
                pd.to_datetime(series.head(50), infer_datetime_format=True)
                col_types[col] = "datetime"
            except (ValueError, TypeError):
                # Cardinality heuristic: if < 10% unique values → categorical
                uniqueness_ratio = series.nunique() / len(series)
                if uniqueness_ratio < 0.10 or series.nunique() <= 20:
                    col_types[col] = "categorical"
                else:
                    col_types[col] = "text"
        else:
            col_types[col] = "other"

    return col_types


# ── Missing Value Analysis ─────────────────────────────────────────────────

def analyze_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with missing value counts and percentages per column.

    WHY: Missing data is the #1 data quality issue in real projects.
    Surfacing this immediately tells the user where they need to clean data.
    """
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df) * 100).round(2)

    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_count.values,
        "Missing %": missing_pct.values,
        "Complete %": (100 - missing_pct).values,
    })

    # Only return columns that have at least some missing data — cleaner UX
    return missing_df[missing_df["Missing Count"] > 0].reset_index(drop=True)


# ── Column-Level Statistics ────────────────────────────────────────────────

def compute_column_stats(df: pd.DataFrame, col_types: Dict[str, str]) -> Dict[str, Dict]:
    """
    Computes relevant statistics for each column based on its semantic type.

    WHY: Numeric stats (mean, std) are meaningless for categorical columns.
    We tailor the stats to what's actually useful per column type.
    """
    stats = {}

    for col in df.columns:
        ctype = col_types.get(col, "other")
        series = df[col].dropna()

        if ctype == "numeric":
            stats[col] = {
                "type": ctype,
                "count": int(series.count()),
                "mean": round(float(series.mean()), 4),
                "median": round(float(series.median()), 4),
                "std": round(float(series.std()), 4),
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "zeros": int((series == 0).sum()),
                "negatives": int((series < 0).sum()),
            }

        elif ctype == "categorical":
            top_values = series.value_counts().head(5).to_dict()
            stats[col] = {
                "type": ctype,
                "count": int(series.count()),
                "unique_values": int(series.nunique()),
                "top_5": top_values,
                "mode": str(series.mode().iloc[0]) if not series.mode().empty else "N/A",
            }

        elif ctype == "datetime":
            try:
                parsed = pd.to_datetime(series)
                stats[col] = {
                    "type": ctype,
                    "count": int(parsed.count()),
                    "min_date": str(parsed.min().date()),
                    "max_date": str(parsed.max().date()),
                    "date_range_days": (parsed.max() - parsed.min()).days,
                }
            except Exception:
                stats[col] = {"type": ctype, "note": "Could not parse dates"}

        elif ctype in ("text", "other"):
            avg_length = series.astype(str).str.len().mean()
            stats[col] = {
                "type": ctype,
                "count": int(series.count()),
                "unique_values": int(series.nunique()),
                "avg_length": round(avg_length, 1),
            }

        elif ctype == "boolean":
            stats[col] = {
                "type": ctype,
                "true_count": int(series.sum()),
                "false_count": int(len(series) - series.sum()),
                "true_pct": round(float(series.mean()) * 100, 2),
            }

        else:
            stats[col] = {"type": ctype}

    return stats


# ── Dataset-Level Summary ──────────────────────────────────────────────────

def generate_dataset_summary(df: pd.DataFrame, col_types: Dict[str, str]) -> Dict[str, Any]:
    """
    High-level summary of the entire dataset.

    WHY: Recruiters and stakeholders want the "executive summary" view —
    rows, columns, memory, duplicates, and a type breakdown at a glance.
    """
    type_counts = {}
    for t in col_types.values():
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "total_cells": df.size,
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
        "total_missing": int(df.isnull().sum().sum()),
        "overall_completeness_pct": round(
            (1 - df.isnull().sum().sum() / df.size) * 100, 2
        ),
        "column_type_breakdown": type_counts,
    }


# ── Master Profile Function ────────────────────────────────────────────────

def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs the full profiling pipeline and returns a structured report.

    This is the single entry point used by app.py.
    Returns everything needed to render the Data Understanding UI.
    """
    col_types = detect_column_types(df)
    missing_df = analyze_missing_values(df)
    col_stats = compute_column_stats(df, col_types)
    summary = generate_dataset_summary(df, col_types)

    return {
        "summary": summary,
        "column_types": col_types,
        "missing_values": missing_df,
        "column_stats": col_stats,
    }