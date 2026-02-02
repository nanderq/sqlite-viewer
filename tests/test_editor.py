"""Tests for the RowEditor class."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from sqlite_viewer.data.database import DatabaseConnection
from sqlite_viewer.data.schema import SchemaInspector
from sqlite_viewer.data.editor import RowEditor, RowData


@pytest.fixture
def sample_db():
    """Create a sample database with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table with various column types
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            age INTEGER,
            balance REAL
        )
    """)

    # Insert some test data
    cursor.executemany(
        "INSERT INTO users (name, email, age, balance) VALUES (?, ?, ?, ?)",
        [
            ("Alice", "alice@example.com", 30, 100.50),
            ("Bob", "bob@example.com", 25, 200.75),
            ("Charlie", None, 35, 50.00),
        ],
    )

    conn.commit()
    conn.close()

    yield db_path

    db_path.unlink()


@pytest.fixture
def db_connection(sample_db):
    """Create a database connection."""
    db = DatabaseConnection(sample_db)
    db.connect()
    yield db
    db.close()


@pytest.fixture
def editor(db_connection):
    """Create a RowEditor instance."""
    schema = SchemaInspector(db_connection)
    return RowEditor(db_connection, schema)


class TestRowEditor:
    """Tests for RowEditor class."""

    def test_get_primary_key_columns(self, editor):
        """Test getting primary key columns."""
        pk_cols = editor.get_primary_key_columns("users")
        assert pk_cols == ["id"]

    def test_insert_row(self, editor, db_connection):
        """Test inserting a new row."""
        editor.insert_row(
            "users",
            {"name": "Dave", "email": "dave@example.com", "age": 40, "balance": 300.0},
        )

        with db_connection.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE name = 'Dave'")
            row = cur.fetchone()
            assert row is not None
            assert row["name"] == "Dave"
            assert row["email"] == "dave@example.com"
            assert row["age"] == 40
            assert row["balance"] == 300.0

    def test_update_row(self, editor, db_connection):
        """Test updating an existing row."""
        editor.update_row(
            "users",
            {"name": "Alice Updated", "age": 31},
            pk_columns=["id"],
            pk_values={"id": 1},
        )

        with db_connection.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = 1")
            row = cur.fetchone()
            assert row["name"] == "Alice Updated"
            assert row["age"] == 31

    def test_delete_row(self, editor, db_connection):
        """Test deleting a row."""
        editor.delete_row("users", pk_columns=["id"], pk_values={"id": 2})

        with db_connection.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = 2")
            row = cur.fetchone()
            assert row is None

    def test_get_row_by_pk(self, editor):
        """Test fetching a row by primary key."""
        row = editor.get_row_by_pk("users", ["id"], {"id": 1})
        assert row is not None
        assert row[1] == "Alice"

    def test_get_row_by_pk_not_found(self, editor):
        """Test fetching a non-existent row."""
        row = editor.get_row_by_pk("users", ["id"], {"id": 999})
        assert row is None

    def test_update_nonexistent_row_raises(self, editor):
        """Test that updating a non-existent row raises an error."""
        with pytest.raises(ValueError, match="No row found"):
            editor.update_row(
                "users",
                {"name": "Ghost"},
                pk_columns=["id"],
                pk_values={"id": 999},
            )

    def test_delete_nonexistent_row_raises(self, editor):
        """Test that deleting a non-existent row raises an error."""
        with pytest.raises(ValueError, match="No row found"):
            editor.delete_row("users", pk_columns=["id"], pk_values={"id": 999})

    def test_insert_empty_values_raises(self, editor):
        """Test that inserting with no values raises an error."""
        with pytest.raises(ValueError, match="No values provided"):
            editor.insert_row("users", {})

    def test_update_empty_values_raises(self, editor):
        """Test that updating with no values raises an error."""
        with pytest.raises(ValueError, match="No values provided"):
            editor.update_row("users", {}, pk_columns=["id"], pk_values={"id": 1})


class TestRowData:
    """Tests for RowData class."""

    def test_empty_row_data(self, editor):
        """Test creating an empty RowData instance."""
        columns = editor.schema.get_columns("users")
        row_data = RowData.empty(columns)

        assert row_data.values["id"] is None
        assert row_data.values["name"] is None
        assert row_data.values["email"] is None

    def test_from_tuple(self, editor):
        """Test creating RowData from a tuple."""
        columns = editor.schema.get_columns("users")
        row_tuple = (1, "Alice", "alice@example.com", 30, 100.50)
        row_data = RowData.from_tuple(columns, row_tuple)

        assert row_data.values["id"] == 1
        assert row_data.values["name"] == "Alice"
        assert row_data.values["email"] == "alice@example.com"
        assert row_data.values["age"] == 30
        assert row_data.values["balance"] == 100.50
