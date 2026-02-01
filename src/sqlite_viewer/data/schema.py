"""Schema introspection for SQLite databases."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .database import DatabaseConnection


@dataclass
class ColumnInfo:
    """Information about a table column."""

    name: str
    type: str
    not_null: bool
    default_value: str | None
    primary_key: bool


@dataclass
class IndexInfo:
    """Information about a table index."""

    name: str
    unique: bool
    columns: list[str]


@dataclass
class ForeignKeyInfo:
    """Information about a foreign key."""

    id: int
    seq: int
    table: str
    from_column: str
    to_column: str
    on_update: str
    on_delete: str


@dataclass
class TableInfo:
    """Complete information about a table."""

    name: str
    columns: list[ColumnInfo]
    indexes: list[IndexInfo]
    foreign_keys: list[ForeignKeyInfo]
    row_count: int


class SchemaInspector:
    """Inspects SQLite database schema."""

    def __init__(self, db: "DatabaseConnection") -> None:
        self.db = db

    def get_tables(self) -> list[str]:
        """Get list of all table names."""
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
            return [row[0] for row in cur.fetchall()]

    def get_columns(self, table_name: str) -> list[ColumnInfo]:
        """Get column information for a table."""
        with self.db.cursor() as cur:
            cur.execute(f"PRAGMA table_info({self._quote_identifier(table_name)})")
            columns = []
            for row in cur.fetchall():
                columns.append(
                    ColumnInfo(
                        name=row[1],
                        type=row[2] or "ANY",
                        not_null=bool(row[3]),
                        default_value=row[4],
                        primary_key=bool(row[5]),
                    )
                )
            return columns

    def get_indexes(self, table_name: str) -> list[IndexInfo]:
        """Get index information for a table."""
        with self.db.cursor() as cur:
            cur.execute(f"PRAGMA index_list({self._quote_identifier(table_name)})")
            indexes = []
            for row in cur.fetchall():
                index_name = row[1]
                unique = bool(row[2])
                # Get columns in this index
                cur.execute(f"PRAGMA index_info({self._quote_identifier(index_name)})")
                columns = [col_row[2] for col_row in cur.fetchall()]
                indexes.append(
                    IndexInfo(
                        name=index_name,
                        unique=unique,
                        columns=columns,
                    )
                )
            return indexes

    def get_foreign_keys(self, table_name: str) -> list[ForeignKeyInfo]:
        """Get foreign key information for a table."""
        with self.db.cursor() as cur:
            cur.execute(f"PRAGMA foreign_key_list({self._quote_identifier(table_name)})")
            fks = []
            for row in cur.fetchall():
                fks.append(
                    ForeignKeyInfo(
                        id=row[0],
                        seq=row[1],
                        table=row[2],
                        from_column=row[3],
                        to_column=row[4],
                        on_update=row[5],
                        on_delete=row[6],
                    )
                )
            return fks

    def get_row_count(self, table_name: str) -> int:
        """Get the number of rows in a table."""
        with self.db.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self._quote_identifier(table_name)}")
            return cur.fetchone()[0]

    def get_table_info(self, table_name: str) -> TableInfo:
        """Get complete information about a table."""
        return TableInfo(
            name=table_name,
            columns=self.get_columns(table_name),
            indexes=self.get_indexes(table_name),
            foreign_keys=self.get_foreign_keys(table_name),
            row_count=self.get_row_count(table_name),
        )

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote an identifier to prevent SQL injection."""
        return f'"{identifier.replace('"', '""')}"'
