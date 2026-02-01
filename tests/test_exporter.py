"""Tests for data export functionality."""

import csv
import json

from sqlite_viewer.data.database import DatabaseConnection
from sqlite_viewer.data.exporter import Exporter


class TestExporter:
    """Tests for Exporter class."""

    def test_export_csv(self, temp_db, tmp_path):
        """Should export table to CSV format."""
        output_path = tmp_path / "users.csv"

        with DatabaseConnection(temp_db) as db:
            exporter = Exporter(db)
            count = exporter.export_csv("users", output_path)

        assert count == 3
        assert output_path.exists()

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["name"] == "Alice"
        assert rows[0]["email"] == "alice@example.com"
        assert rows[1]["name"] == "Bob"
        assert rows[2]["name"] == "Charlie"

    def test_export_json(self, temp_db, tmp_path):
        """Should export table to JSON format."""
        output_path = tmp_path / "orders.json"

        with DatabaseConnection(temp_db) as db:
            exporter = Exporter(db)
            count = exporter.export_json("orders", output_path)

        assert count == 4
        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)

        assert len(data) == 4
        assert data[0]["total"] == 99.99
        assert data[0]["status"] == "completed"

    def test_export_csv_with_null(self, temp_db, tmp_path):
        """Should handle NULL values in CSV export."""
        output_path = tmp_path / "users.csv"

        with DatabaseConnection(temp_db) as db:
            exporter = Exporter(db)
            exporter.export_csv("users", output_path)

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Bob has NULL bio
        bob = next(r for r in rows if r["name"] == "Bob")
        assert bob["bio"] == ""

    def test_export_json_with_null(self, temp_db, tmp_path):
        """Should handle NULL values in JSON export."""
        output_path = tmp_path / "users.json"

        with DatabaseConnection(temp_db) as db:
            exporter = Exporter(db)
            exporter.export_json("users", output_path)

        with open(output_path) as f:
            data = json.load(f)

        bob = next(r for r in data if r["name"] == "Bob")
        assert bob["bio"] is None

    def test_export_csv_with_blob(self, temp_db, tmp_path):
        """Should handle BLOB values in CSV export."""
        output_path = tmp_path / "blobs.csv"

        with DatabaseConnection(temp_db) as db:
            exporter = Exporter(db)
            exporter.export_csv("blobs", output_path)

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "[BLOB:6B]" in rows[0]["data"]

    def test_export_json_with_blob(self, temp_db, tmp_path):
        """Should handle BLOB values in JSON export."""
        output_path = tmp_path / "blobs.json"

        with DatabaseConnection(temp_db) as db:
            exporter = Exporter(db)
            exporter.export_json("blobs", output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert "[BLOB:6B]" in data[0]["data"]

    def test_export_empty_table(self, empty_db, tmp_path):
        """Should handle empty tables."""
        csv_path = tmp_path / "empty.csv"
        json_path = tmp_path / "empty.json"

        with DatabaseConnection(empty_db) as db:
            exporter = Exporter(db)
            csv_count = exporter.export_csv("empty_table", csv_path)
            json_count = exporter.export_json("empty_table", json_path)

        assert csv_count == 0
        assert json_count == 0

        # CSV should have header only
        with open(csv_path) as f:
            content = f.read()
        assert "id" in content

        # JSON should be empty array
        with open(json_path) as f:
            data = json.load(f)
        assert data == []

    def test_export_large_table(self, large_table_db, tmp_path):
        """Should handle large tables with streaming."""
        output_path = tmp_path / "items.csv"

        with DatabaseConnection(large_table_db) as db:
            exporter = Exporter(db)
            count = exporter.export_csv("items", output_path)

        assert count == 250

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 250
