"""Pytest fixtures for sqlite_viewer tests."""

import sqlite3
import pytest
from pathlib import Path


@pytest.fixture
def temp_db(tmp_path) -> Path:
    """Create a temporary SQLite database with test data."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            bio TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total REAL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE blobs (
            id INTEGER PRIMARY KEY,
            data BLOB
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_orders_user ON orders(user_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_users_email ON users(email)")

    # Insert test data
    cursor.executemany(
        "INSERT INTO users (name, email, bio) VALUES (?, ?, ?)",
        [
            ("Alice", "alice@example.com", "Hello world"),
            ("Bob", "bob@example.com", None),
            ("Charlie", "charlie@example.com", "A" * 100),
        ],
    )

    cursor.executemany(
        "INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)",
        [
            (1, 99.99, "completed"),
            (1, 149.50, "pending"),
            (2, 75.00, "completed"),
            (3, 200.00, "shipped"),
        ],
    )

    cursor.execute(
        "INSERT INTO blobs (data) VALUES (?)",
        (b"\x00\x01\x02\x03\x04\x05",),
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def empty_db(tmp_path) -> Path:
    """Create an empty SQLite database."""
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE empty_table (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def large_table_db(tmp_path) -> Path:
    """Create a database with a large table for pagination testing."""
    db_path = tmp_path / "large.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT)")
    conn.executemany(
        "INSERT INTO items (value) VALUES (?)",
        [(f"item_{i}",) for i in range(250)],
    )
    conn.commit()
    conn.close()
    return db_path
