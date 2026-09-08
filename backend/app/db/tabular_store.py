"""
KavachAI — Structured/Tabular Data Store
Implements: FR-ING-7 (CSV/XLSX -> structured store), FR-DAT-1 (time-series retrieval)

Schema per row: timestamp, equipment_id, metric, value, unit
Each dataset gets its own SQLite table for isolation and queryability.
Data Agent (Phase 5) queries this store using pandas — never the LLM.
"""

import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.config import settings


class TabularStore:
    """SQLite-backed structured data store for time-series datasets."""

    REQUIRED_COLUMNS = {"timestamp", "equipment_id", "metric", "value", "unit"}

    def __init__(self):
        # Use the same SQLite DB file for simplicity
        self.db_path = settings.SQLITE_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn


    def ingest_dataframe(self, dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Store a DataFrame as a named SQLite table.
        Implements: FR-ING-7

        Args:
            dataset_id: unique dataset identifier (becomes the table name prefix)
            df: pandas DataFrame with required columns

        Returns:
            {table_name, row_count, columns}

        Raises:
            ValueError if required columns are missing
        """
        # Validate required columns
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}. "
                             f"Expected: {self.REQUIRED_COLUMNS}")

        table_name = f"dataset_{dataset_id.replace('-', '_')}"

        conn = self._get_connection()
        try:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            return {
                "table_name": table_name,
                "row_count": len(df),
                "columns": list(df.columns),
            }
        finally:
            conn.close()

    def query_by_equipment(
        self,
        table_name: str,
        equipment_id: str,
        metric: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query dataset rows for a specific equipment and optionally a metric.
        Implements: FR-DAT-1

        Returns:
            DataFrame of matching rows, sorted by timestamp
        """
        conn = self._get_connection()
        try:
            query = f"SELECT * FROM [{table_name}] WHERE equipment_id = ?"
            params: list = [equipment_id]

            if metric:
                query += " AND metric = ?"
                params.append(metric)

            query += " ORDER BY timestamp ASC"

            return pd.read_sql_query(query, conn, params=params)
        finally:
            conn.close()

    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get row count and column info for a dataset table."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            row_count = cursor.fetchone()[0]

            cursor = conn.execute(f"PRAGMA table_info([{table_name}])")
            columns = [row[1] for row in cursor.fetchall()]

            return {"table_name": table_name, "row_count": row_count, "columns": columns}
        except Exception:
            return None
        finally:
            conn.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if a dataset table exists."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()


# Singleton instance
tabular_store = TabularStore()
