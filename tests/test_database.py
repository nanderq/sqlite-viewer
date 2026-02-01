"""Tests for database connection and validation."""

from pathlib import Path

from sqlite_viewer.data.database import DatabaseConnection, validate_sqlite_file


class TestValidateSQLiteFile:
    """Tests for validate_sqlite_file function."""

    def test_valid_sqlite_file(self, temp_db):
        """Should return True for a valid SQLite database."""
        assert validate_sqlite_file(temp_db) is True

    def test_nonexistent_file(self, tmp_path):
        """Should return False for a file that doesn't exist."""
        assert validate_sqlite_file(tmp_path / "nonexistent.db") is False

    def test_directory(self, tmp_path):
        """Should return False for a directory."""
        assert validate_sqlite_file(tmp_path) is False

    def test_non_sqlite_file(self, tmp_path):
        """Should return False for a non-SQLite file."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello, world!")
        assert validate_sqlite_file(text_file) is False

    def test_empty_file(self, tmp_path):
        """Should return False for an empty file."""
        empty_file = tmp_path / "empty.db"
        empty_file.touch()
        assert validate_sqlite_file(empty_file) is False


class TestDatabaseConnection:
    """Tests for DatabaseConnection class."""

    def test_connect_and_close(self, temp_db):
        """Should connect and close without errors."""
        db = DatabaseConnection(temp_db)
        db.connect()
        assert db._connection is not None
        db.close()
        assert db._connection is None

    def test_context_manager(self, temp_db):
        """Should work as a context manager."""
        with DatabaseConnection(temp_db) as db:
            assert db._connection is not None
        assert db._connection is None

    def test_cursor_context_manager(self, temp_db):
        """Should provide cursor via context manager."""
        db = DatabaseConnection(temp_db)
        db.connect()
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            assert count == 3
        db.close()

    def test_connection_property_auto_connects(self, temp_db):
        """Connection property should auto-connect if not connected."""
        db = DatabaseConnection(temp_db)
        assert db._connection is None
        conn = db.connection
        assert conn is not None
        assert db._connection is not None
        db.close()

    def test_multiple_connect_calls_safe(self, temp_db):
        """Multiple connect calls should be safe."""
        db = DatabaseConnection(temp_db)
        db.connect()
        conn1 = db._connection
        db.connect()
        conn2 = db._connection
        assert conn1 is conn2
        db.close()
