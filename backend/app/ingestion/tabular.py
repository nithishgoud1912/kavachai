"""
KavachAI — Tabular Data Ingestion (CSV/XLSX)
Implements: FR-ING-7 (parse CSV/XLSX into structured store with column semantics)

Schema: timestamp, equipment_id, metric, value, unit
Parsed via pandas, stored in the TabularStore.
"""

import io
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from app.db.tabular_store import tabular_store


def parse_tabular_file(
    file_content: bytes,
    filename: str,
    dataset_id: str,
) -> Dict[str, Any]:
    """
    Parse a CSV/XLSX file and store in the structured tabular store.
    Implements: FR-ING-7

    Expected columns: timestamp, equipment_id, metric, value, unit
    Column names are case-insensitive and will be normalized.

    Args:
        file_content: raw file bytes
        filename: original filename
        dataset_id: unique dataset identifier

    Returns:
        {dataset_id, table_name, row_count, columns, status}

    Raises:
        ValueError if the file format is unsupported or required columns are missing
    """
    suffix = Path(filename).suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(io.BytesIO(file_content))
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(io.BytesIO(file_content))
    else:
        raise ValueError(f"Unsupported tabular format: {suffix}. Expected .csv or .xlsx")

    # Normalize column names: lowercase, strip whitespace
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Validate required columns
    required = {"timestamp", "equipment_id", "metric", "value", "unit"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Expected: {required}"
        )

    # Ensure value column is numeric
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Drop rows with NaN values (from coercion failures)
    df = df.dropna(subset=["value"])

    # Store in tabular store
    result = tabular_store.ingest_dataframe(dataset_id, df)

    return {
        "dataset_id": dataset_id,
        "table_name": result["table_name"],
        "row_count": result["row_count"],
        "columns": result["columns"],
        "status": "ready",
    }
