"""Tests for schema introspection."""

from sqlite_viewer.data.database import DatabaseConnection
from sqlite_viewer.data.schema import SchemaInspector


class TestSchemaInspector:
    """Tests for SchemaInspector class."""

    def test_get_tables(self, temp_db):
        """Should return all user tables."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            tables = inspector.get_tables()
            assert set(tables) == {"users", "orders", "blobs"}

    def test_get_tables_excludes_sqlite_tables(self, temp_db):
        """Should not return internal sqlite tables."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            tables = inspector.get_tables()
            assert not any(t.startswith("sqlite_") for t in tables)

    def test_get_columns(self, temp_db):
        """Should return column information."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            columns = inspector.get_columns("users")

            assert len(columns) == 5

            id_col = next(c for c in columns if c.name == "id")
            assert id_col.type == "INTEGER"
            assert id_col.primary_key is True

            name_col = next(c for c in columns if c.name == "name")
            assert name_col.type == "TEXT"
            assert name_col.not_null is True

            email_col = next(c for c in columns if c.name == "email")
            assert email_col.type == "TEXT"
            assert email_col.not_null is False

    def test_get_indexes(self, temp_db):
        """Should return index information."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            indexes = inspector.get_indexes("orders")

            assert len(indexes) >= 1
            user_idx = next(i for i in indexes if i.name == "idx_orders_user")
            assert user_idx.unique is False
            assert user_idx.columns == ["user_id"]

    def test_get_unique_index(self, temp_db):
        """Should correctly identify unique indexes."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            indexes = inspector.get_indexes("users")

            email_idx = next(i for i in indexes if i.name == "idx_users_email")
            assert email_idx.unique is True
            assert email_idx.columns == ["email"]

    def test_get_foreign_keys(self, temp_db):
        """Should return foreign key information."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            fks = inspector.get_foreign_keys("orders")

            assert len(fks) == 1
            fk = fks[0]
            assert fk.table == "users"
            assert fk.from_column == "user_id"
            assert fk.to_column == "id"

    def test_get_foreign_keys_empty(self, temp_db):
        """Should return empty list for tables without foreign keys."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            fks = inspector.get_foreign_keys("users")
            assert fks == []

    def test_get_row_count(self, temp_db):
        """Should return correct row count."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            assert inspector.get_row_count("users") == 3
            assert inspector.get_row_count("orders") == 4
            assert inspector.get_row_count("blobs") == 1

    def test_get_table_info(self, temp_db):
        """Should return complete table information."""
        with DatabaseConnection(temp_db) as db:
            inspector = SchemaInspector(db)
            info = inspector.get_table_info("orders")

            assert info.name == "orders"
            assert len(info.columns) == 4
            assert len(info.indexes) >= 1
            assert len(info.foreign_keys) == 1
            assert info.row_count == 4
