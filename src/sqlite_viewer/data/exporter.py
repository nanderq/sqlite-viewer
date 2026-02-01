"""Export data to CSV and JSON formats."""

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from .database import DatabaseConnection


class Exporter:
    """Exports table data to various formats."""

    def __init__(self, db: "DatabaseConnection") -> None:
        self.db = db

    def _stream_table(
        self, table_name: str, batch_size: int = 1000
    ) -> Iterator[tuple[list[str], list[tuple[Any, ...]]]]:
        """Stream table data in batches. Yields (columns, rows) tuples."""
        with self.db.cursor() as cur:
            # Get column names
            cur.execute(f"SELECT * FROM {self._quote_identifier(table_name)} LIMIT 0")
            columns = [desc[0] for desc in cur.description] if cur.description else []

            # Stream rows in batches
            offset = 0
            while True:
                cur.execute(
                    f"SELECT * FROM {self._quote_identifier(table_name)} "
                    f"LIMIT ? OFFSET ?",
                    (batch_size, offset),
                )
                rows = [tuple(row) for row in cur.fetchall()]
                if not rows:
                    break
                yield columns, rows
                offset += batch_size

    def export_csv(self, table_name: str, output_path: Path) -> int:
        """Export table to CSV file. Returns number of rows exported."""
        row_count = 0
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer: csv.writer | None = None
            for columns, rows in self._stream_table(table_name):
                if writer is None:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                for row in rows:
                    # Convert bytes to hex string for CSV
                    processed_row = [
                        self._format_value_for_csv(val) for val in row
                    ]
                    writer.writerow(processed_row)
                    row_count += 1
        return row_count

    def export_json(self, table_name: str, output_path: Path) -> int:
        """Export table to JSON file. Returns number of rows exported."""
        row_count = 0
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("[\n")
            first = True
            for columns, rows in self._stream_table(table_name):
                for row in rows:
                    if not first:
                        f.write(",\n")
                    first = False
                    # Create dict with column names as keys
                    row_dict = {
                        col: self._format_value_for_json(val)
                        for col, val in zip(columns, row)
                    }
                    f.write("  " + json.dumps(row_dict, ensure_ascii=False))
                    row_count += 1
            f.write("\n]\n")
        return row_count

    @staticmethod
    def _format_value_for_csv(value: Any) -> str:
        """Format a value for CSV export."""
        if value is None:
            return ""
        if isinstance(value, bytes):
            return f"[BLOB:{len(value)}B]"
        return str(value)

    @staticmethod
    def _format_value_for_json(value: Any) -> Any:
        """Format a value for JSON export."""
        if isinstance(value, bytes):
            return f"[BLOB:{len(value)}B]"
        return value

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote an identifier to prevent SQL injection."""
        return f'"{identifier.replace('"', '""')}"'
