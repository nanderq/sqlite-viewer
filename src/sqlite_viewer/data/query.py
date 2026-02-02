"""Query execution with pagination support."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .database import DatabaseConnection


@dataclass
class PageResult:
    """Result of a paginated query."""

    rows: list[tuple[Any, ...]]
    columns: list[str]
    page: int
    page_size: int
    total_rows: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.total_rows == 0:
            return 1
        return (self.total_rows + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    @property
    def start_row(self) -> int:
        """Get the 1-indexed start row number."""
        if self.total_rows == 0:
            return 0
        return (self.page - 1) * self.page_size + 1

    @property
    def end_row(self) -> int:
        """Get the 1-indexed end row number."""
        return min(self.page * self.page_size, self.total_rows)


class PaginatedQuery:
    """Executes paginated queries on a table."""

    DEFAULT_PAGE_SIZE = 50

    def __init__(self, db: "DatabaseConnection", table_name: str) -> None:
        self.db = db
        self.table_name = table_name
        self._total_rows: int | None = None

    @property
    def total_rows(self) -> int:
        """Get total row count (cached)."""
        if self._total_rows is None:
            with self.db.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) FROM {self._quote_identifier(self.table_name)}"
                )
                self._total_rows = cur.fetchone()[0]
        return self._total_rows

    def invalidate_cache(self) -> None:
        """Invalidate the row count cache."""
        self._total_rows = None

    def fetch_page(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> PageResult:
        """Fetch a page of results."""
        page = max(1, page)
        page_size = max(1, min(page_size, 1000))  # Cap at 1000 rows per page
        offset = (page - 1) * page_size

        with self.db.cursor() as cur:
            # Get column names
            cur.execute(
                f"SELECT * FROM {self._quote_identifier(self.table_name)} LIMIT 0"
            )
            columns = [desc[0] for desc in cur.description] if cur.description else []

            # Fetch the page
            cur.execute(
                f"SELECT * FROM {self._quote_identifier(self.table_name)} "
                f"LIMIT ? OFFSET ?",
                (page_size, offset),
            )
            rows = [tuple(row) for row in cur.fetchall()]

        return PageResult(
            rows=rows,
            columns=columns,
            page=page,
            page_size=page_size,
            total_rows=self.total_rows,
        )

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote an identifier to prevent SQL injection."""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'
