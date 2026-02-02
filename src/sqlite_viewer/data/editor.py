"""Database row editing operations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .database import DatabaseConnection
    from .schema import SchemaInspector, ColumnInfo


@dataclass
class RowData:
    """Represents a row's data with column metadata."""

    columns: list["ColumnInfo"]
    values: dict[str, Any]

    @classmethod
    def empty(cls, columns: list["ColumnInfo"]) -> "RowData":
        """Create an empty row with default values."""
        values = {}
        for col in columns:
            if col.default_value is not None:
                values[col.name] = col.default_value
            else:
                values[col.name] = None
        return cls(columns=columns, values=values)

    @classmethod
    def from_tuple(cls, columns: list["ColumnInfo"], row: tuple[Any, ...]) -> "RowData":
        """Create from a tuple of values."""
        values = {col.name: val for col, val in zip(columns, row)}
        return cls(columns=columns, values=values)


class RowEditor:
    """Handles row editing operations (INSERT, UPDATE, DELETE)."""

    def __init__(self, db: "DatabaseConnection", schema: "SchemaInspector") -> None:
        self.db = db
        self.schema = schema

    def insert_row(self, table_name: str, values: dict[str, Any]) -> None:
        """Insert a new row into the table."""
        if not values:
            raise ValueError("No values provided for insert")

        columns = list(values.keys())
        placeholders = ", ".join("?" for _ in columns)
        column_names = ", ".join(self._quote_identifier(c) for c in columns)

        sql = (
            f"INSERT INTO {self._quote_identifier(table_name)} "
            f"({column_names}) VALUES ({placeholders})"
        )

        with self.db.cursor() as cur:
            cur.execute(sql, tuple(values.values()))
            self.db.connection.commit()

    def update_row(
        self,
        table_name: str,
        values: dict[str, Any],
        pk_columns: list[str],
        pk_values: dict[str, Any],
    ) -> None:
        """Update an existing row."""
        if not values:
            raise ValueError("No values provided for update")
        if not pk_columns or not pk_values:
            raise ValueError("Primary key required for update")

        # Build SET clause
        set_parts = [f"{self._quote_identifier(k)} = ?" for k in values.keys()]
        set_clause = ", ".join(set_parts)

        # Build WHERE clause for primary key
        where_parts = [f"{self._quote_identifier(k)} = ?" for k in pk_columns]
        where_clause = " AND ".join(where_parts)

        sql = (
            f"UPDATE {self._quote_identifier(table_name)} "
            f"SET {set_clause} "
            f"WHERE {where_clause}"
        )

        # Combine values for SET and WHERE clauses
        params = tuple(values.values()) + tuple(pk_values[k] for k in pk_columns)

        with self.db.cursor() as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                raise ValueError("No row found with the specified primary key")
            self.db.connection.commit()

    def delete_row(
        self,
        table_name: str,
        pk_columns: list[str],
        pk_values: dict[str, Any],
    ) -> None:
        """Delete a row from the table."""
        if not pk_columns or not pk_values:
            raise ValueError("Primary key required for delete")

        # Build WHERE clause for primary key
        where_parts = [f"{self._quote_identifier(k)} = ?" for k in pk_columns]
        where_clause = " AND ".join(where_parts)

        sql = f"DELETE FROM {self._quote_identifier(table_name)} WHERE {where_clause}"
        params = tuple(pk_values[k] for k in pk_columns)

        with self.db.cursor() as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                raise ValueError("No row found with the specified primary key")
            self.db.connection.commit()

    def get_primary_key_columns(self, table_name: str) -> list[str]:
        """Get the primary key column names for a table."""
        columns = self.schema.get_columns(table_name)
        return [col.name for col in columns if col.primary_key]

    def get_row_by_pk(
        self, table_name: str, pk_columns: list[str], pk_values: dict[str, Any]
    ) -> tuple[Any, ...] | None:
        """Fetch a single row by its primary key."""
        if not pk_columns or not pk_values:
            return None

        where_parts = [f"{self._quote_identifier(k)} = ?" for k in pk_columns]
        where_clause = " AND ".join(where_parts)

        sql = f"SELECT * FROM {self._quote_identifier(table_name)} WHERE {where_clause}"
        params = tuple(pk_values[k] for k in pk_columns)

        with self.db.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return tuple(row) if row else None

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote an identifier to prevent SQL injection."""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'
