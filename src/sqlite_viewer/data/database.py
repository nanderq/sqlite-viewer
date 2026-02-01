"""SQLite connection manager."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class DatabaseConnection:
    """Manages SQLite database connections."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open a connection to the database."""
        if self._connection is not None:
            return
        self._connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the active connection, connecting if necessary."""
        if self._connection is None:
            self.connect()
        return self._connection

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        """Context manager for database cursors."""
        cur = self.connection.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def __enter__(self) -> "DatabaseConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def validate_sqlite_file(path: Path) -> bool:
    """Check if a file is a valid SQLite database."""
    if not path.exists():
        return False
    if not path.is_file():
        return False
    # Check SQLite magic header
    try:
        with open(path, "rb") as f:
            header = f.read(16)
            return header[:16] == b"SQLite format 3\x00"
    except (OSError, IOError):
        return False
