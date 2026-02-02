"""Paginated data table widget."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.widgets import DataTable, Button, Static

from sqlite_viewer.data.query import PaginatedQuery, PageResult
from sqlite_viewer.utils.formatters import format_cell_value


class PaginationBar(Horizontal):
    """Pagination controls bar."""

    DEFAULT_CSS = """
    PaginationBar {
        height: 3;
        padding: 0 1;
        align: center middle;
        background: $surface;
    }
    PaginationBar Button {
        min-width: 10;
        margin: 0 1;
    }
    PaginationBar .page-info {
        width: auto;
        padding: 0 2;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._page_info = ""

    def compose(self) -> ComposeResult:
        yield Button("◀ Prev", id="prev-page", variant="default")
        yield Static("", id="page-info", classes="page-info")
        yield Button("Next ▶", id="next-page", variant="default")

    def update_info(self, result: PageResult) -> None:
        """Update the pagination info display."""
        info = self.query_one("#page-info", Static)
        if result.total_rows == 0:
            info.update("No rows")
        else:
            info.update(
                f"Page {result.page} of {result.total_pages} | "
                f"Rows {result.start_row}-{result.end_row} of {result.total_rows}"
            )

        # Enable/disable buttons
        self.query_one("#prev-page", Button).disabled = not result.has_previous
        self.query_one("#next-page", Button).disabled = not result.has_next


class PaginatedDataTable(Vertical):
    """DataTable with pagination support."""

    DEFAULT_CSS = """
    PaginatedDataTable {
        height: 100%;
    }
    PaginatedDataTable > DataTable {
        height: 1fr;
    }
    """

    class RowEditRequested(Message):
        """Posted when user requests to edit a row."""

        def __init__(self, row_index: int, row_data: tuple[Any, ...], columns: list[str]) -> None:
            super().__init__()
            self.row_index = row_index
            self.row_data = row_data
            self.columns = columns

    class RowDeleteRequested(Message):
        """Posted when user requests to delete a row."""

        def __init__(self, row_index: int, row_data: tuple[Any, ...], columns: list[str]) -> None:
            super().__init__()
            self.row_index = row_index
            self.row_data = row_data
            self.columns = columns

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._query: PaginatedQuery | None = None
        self._current_page = 1
        self._page_size = 50
        self._result: PageResult | None = None

    def compose(self) -> ComposeResult:
        yield DataTable(id="data-table")
        yield PaginationBar(id="pagination")

    def set_query(self, query: PaginatedQuery) -> None:
        """Set the query source and load first page."""
        self._query = query
        self._current_page = 1
        self._load_page()

    def _load_page(self) -> None:
        """Load the current page of data."""
        if self._query is None:
            return

        self._result = self._query.fetch_page(self._current_page, self._page_size)
        table = self.query_one("#data-table", DataTable)

        # Clear and set up columns
        table.clear(columns=True)
        for col in self._result.columns:
            table.add_column(col, key=col)

        # Add rows
        for row in self._result.rows:
            formatted = [format_cell_value(val) for val in row]
            table.add_row(*formatted)

        # Update pagination bar
        pagination = self.query_one("#pagination", PaginationBar)
        pagination.update_info(self._result)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle pagination button presses."""
        if event.button.id == "prev-page" and self._result and self._result.has_previous:
            self._current_page -= 1
            self._load_page()
        elif event.button.id == "next-page" and self._result and self._result.has_next:
            self._current_page += 1
            self._load_page()

    def refresh_data(self) -> None:
        """Refresh the current page data."""
        if self._query:
            self._query.invalidate_cache()
            self._load_page()

    def get_selected_row(self) -> tuple[int, tuple[Any, ...], list[str]] | None:
        """Get the currently selected row data.

        Returns:
            Tuple of (row_index, row_data, columns) or None if no selection.
        """
        if self._result is None or not self._result.rows:
            return None

        table = self.query_one("#data-table", DataTable)
        if table.cursor_row is None or table.cursor_row >= len(self._result.rows):
            return None

        row_index = table.cursor_row
        row_data = self._result.rows[row_index]
        return (row_index, row_data, self._result.columns)

    def request_edit_selected(self) -> None:
        """Request to edit the currently selected row."""
        selection = self.get_selected_row()
        if selection:
            row_index, row_data, columns = selection
            self.post_message(self.RowEditRequested(row_index, row_data, columns))

    def request_delete_selected(self) -> None:
        """Request to delete the currently selected row."""
        selection = self.get_selected_row()
        if selection:
            row_index, row_data, columns = selection
            self.post_message(self.RowDeleteRequested(row_index, row_data, columns))
