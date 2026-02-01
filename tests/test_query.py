"""Tests for query execution and pagination."""

from sqlite_viewer.data.database import DatabaseConnection
from sqlite_viewer.data.query import PaginatedQuery


class TestPaginatedQuery:
    """Tests for PaginatedQuery class."""

    def test_fetch_first_page(self, temp_db):
        """Should fetch the first page of results."""
        with DatabaseConnection(temp_db) as db:
            query = PaginatedQuery(db, "users")
            result = query.fetch_page(page=1, page_size=10)

            assert result.page == 1
            assert result.page_size == 10
            assert result.total_rows == 3
            assert len(result.rows) == 3
            assert result.columns == ["id", "name", "email", "bio", "created_at"]

    def test_pagination_with_large_table(self, large_table_db):
        """Should paginate correctly with large tables."""
        with DatabaseConnection(large_table_db) as db:
            query = PaginatedQuery(db, "items")

            # First page
            result1 = query.fetch_page(page=1, page_size=50)
            assert result1.page == 1
            assert result1.total_rows == 250
            assert len(result1.rows) == 50
            assert result1.total_pages == 5
            assert result1.has_next is True
            assert result1.has_previous is False

            # Middle page
            result3 = query.fetch_page(page=3, page_size=50)
            assert result3.page == 3
            assert len(result3.rows) == 50
            assert result3.has_next is True
            assert result3.has_previous is True

            # Last page
            result5 = query.fetch_page(page=5, page_size=50)
            assert result5.page == 5
            assert len(result5.rows) == 50
            assert result5.has_next is False
            assert result5.has_previous is True

    def test_page_result_properties(self, large_table_db):
        """Should calculate page result properties correctly."""
        with DatabaseConnection(large_table_db) as db:
            query = PaginatedQuery(db, "items")
            result = query.fetch_page(page=2, page_size=50)

            assert result.start_row == 51
            assert result.end_row == 100
            assert result.total_pages == 5

    def test_empty_table(self, empty_db):
        """Should handle empty tables correctly."""
        with DatabaseConnection(empty_db) as db:
            query = PaginatedQuery(db, "empty_table")
            result = query.fetch_page(page=1, page_size=50)

            assert result.total_rows == 0
            assert len(result.rows) == 0
            assert result.total_pages == 1
            assert result.start_row == 0
            assert result.end_row == 0
            assert result.has_next is False
            assert result.has_previous is False

    def test_page_clamping(self, temp_db):
        """Should clamp invalid page numbers."""
        with DatabaseConnection(temp_db) as db:
            query = PaginatedQuery(db, "users")

            # Page 0 should become page 1
            result = query.fetch_page(page=0, page_size=10)
            assert result.page == 1

            # Negative page should become page 1
            result = query.fetch_page(page=-5, page_size=10)
            assert result.page == 1

    def test_page_size_clamping(self, temp_db):
        """Should clamp page size to reasonable limits."""
        with DatabaseConnection(temp_db) as db:
            query = PaginatedQuery(db, "users")

            # Very large page size should be capped at 1000
            result = query.fetch_page(page=1, page_size=10000)
            assert result.page_size == 1000

            # Zero page size should become 1
            result = query.fetch_page(page=1, page_size=0)
            assert result.page_size == 1

    def test_invalidate_cache(self, temp_db):
        """Should invalidate row count cache."""
        with DatabaseConnection(temp_db) as db:
            query = PaginatedQuery(db, "users")

            # Access total_rows to cache it
            assert query.total_rows == 3
            assert query._total_rows == 3

            # Invalidate
            query.invalidate_cache()
            assert query._total_rows is None

            # Should recalculate
            assert query.total_rows == 3
