"""Main Textual application for SQLite Viewer."""

import sys
from pathlib import Path
from typing import Any

import click
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, TabbedContent, TabPane, Static, DataTable

from sqlite_viewer.data.database import DatabaseConnection, validate_sqlite_file
from sqlite_viewer.data.schema import SchemaInspector
from sqlite_viewer.data.query import PaginatedQuery
from sqlite_viewer.data.exporter import Exporter
from sqlite_viewer.data.editor import RowEditor, RowData
from sqlite_viewer.widgets.table_tree import TableTree
from sqlite_viewer.widgets.data_table import PaginatedDataTable
from sqlite_viewer.screens.export_dialog import ExportDialog
from sqlite_viewer.screens.row_editor import RowEditorScreen, RowEditorResult, EditMode
from sqlite_viewer.screens.confirm_dialog import ConfirmDialog


class SQLiteViewerApp(App):
    """A TUI application for viewing SQLite databases."""

    TITLE = "SQLite Viewer"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("e", "export", "Export"),
        Binding("r", "refresh", "Refresh"),
        Binding("a", "add_row", "Add Row"),
        Binding("enter", "edit_row", "Edit Row", show=False),
        Binding("d", "delete_row", "Delete"),
        Binding("tab", "focus_next", "Focus Next", show=False),
        Binding("shift+tab", "focus_previous", "Focus Prev", show=False),
    ]

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self.db = DatabaseConnection(db_path)
        self.schema = SchemaInspector(self.db)
        self.exporter = Exporter(self.db)
        self.editor = RowEditor(self.db, self.schema)
        self._current_table: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="sidebar"):
                yield TableTree(self.schema, id="table-tree")
            with Vertical(id="content"):
                with TabbedContent(id="content-tabs"):
                    with TabPane("Data", id="data-tab"):
                        yield PaginatedDataTable(id="data-view")
                    with TabPane("Schema", id="schema-tab"):
                        yield Static("Select a table to view schema", id="schema-content", classes="no-selection")
                    with TabPane("Indexes", id="indexes-tab"):
                        yield Static("Select a table to view indexes", id="indexes-content", classes="no-selection")
                    with TabPane("Foreign Keys", id="fk-tab"):
                        yield Static("Select a table to view foreign keys", id="fk-content", classes="no-selection")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app on mount."""
        self.db.connect()
        self.sub_title = self.db_path.name

    def on_unmount(self) -> None:
        """Clean up on unmount."""
        self.db.close()

    def on_table_tree_table_selected(self, event: TableTree.TableSelected) -> None:
        """Handle table selection from the tree."""
        self._current_table = event.table_name
        self._load_table_data(event.table_name)
        self._load_schema_info(event.table_name)

    def _load_table_data(self, table_name: str) -> None:
        """Load data for the selected table."""
        query = PaginatedQuery(self.db, table_name)
        data_view = self.query_one("#data-view", PaginatedDataTable)
        data_view.set_query(query)

    def _load_schema_info(self, table_name: str) -> None:
        """Load schema information for the selected table."""
        table_info = self.schema.get_table_info(table_name)

        # Update schema tab
        schema_content = self.query_one("#schema-content", Static)
        schema_lines = ["[bold]Columns:[/bold]\n"]
        for col in table_info.columns:
            pk = " 🔑 PRIMARY KEY" if col.primary_key else ""
            nn = " NOT NULL" if col.not_null else ""
            default = f" DEFAULT {col.default_value}" if col.default_value else ""
            schema_lines.append(f"  [cyan]{col.name}[/cyan] [green]{col.type}[/green]{pk}{nn}{default}")
        schema_content.update("\n".join(schema_lines))

        # Update indexes tab
        indexes_content = self.query_one("#indexes-content", Static)
        if table_info.indexes:
            idx_lines = ["[bold]Indexes:[/bold]\n"]
            for idx in table_info.indexes:
                unique = " [yellow]UNIQUE[/yellow]" if idx.unique else ""
                cols = ", ".join(idx.columns)
                idx_lines.append(f"  [cyan]{idx.name}[/cyan]{unique}\n    Columns: {cols}")
            indexes_content.update("\n".join(idx_lines))
        else:
            indexes_content.update("[dim]No indexes defined[/dim]")

        # Update foreign keys tab
        fk_content = self.query_one("#fk-content", Static)
        if table_info.foreign_keys:
            fk_lines = ["[bold]Foreign Keys:[/bold]\n"]
            for fk in table_info.foreign_keys:
                fk_lines.append(
                    f"  [cyan]{fk.from_column}[/cyan] → "
                    f"[green]{fk.table}[/green].[cyan]{fk.to_column}[/cyan]\n"
                    f"    ON UPDATE {fk.on_update}, ON DELETE {fk.on_delete}"
                )
            fk_content.update("\n".join(fk_lines))
        else:
            fk_content.update("[dim]No foreign keys defined[/dim]")

    def action_export(self) -> None:
        """Show the export dialog."""
        if self._current_table is None:
            self.notify("Please select a table first", severity="warning")
            return

        def handle_export(result: tuple[str, Path] | None) -> None:
            if result is None:
                return
            format_type, filepath = result
            try:
                if format_type == "csv":
                    count = self.exporter.export_csv(self._current_table, filepath)
                else:
                    count = self.exporter.export_json(self._current_table, filepath)
                self.notify(f"Exported {count} rows to {filepath}", severity="information")
            except Exception as e:
                self.notify(f"Export failed: {e}", severity="error")

        self.push_screen(ExportDialog(self._current_table), handle_export)

    def action_refresh(self) -> None:
        """Refresh the current table data."""
        if self._current_table:
            self._load_table_data(self._current_table)
            self._load_schema_info(self._current_table)
            self.notify("Data refreshed", severity="information")

    def action_add_row(self) -> None:
        """Show the add row dialog."""
        if self._current_table is None:
            self.notify("Please select a table first", severity="warning")
            return

        columns = self.schema.get_columns(self._current_table)
        pk_columns = self.editor.get_primary_key_columns(self._current_table)

        self.push_screen(
            RowEditorScreen(
                table_name=self._current_table,
                columns=columns,
                mode=EditMode.ADD,
                pk_columns=pk_columns,
            ),
            self._handle_row_editor_result,
        )

    def action_edit_row(self) -> None:
        """Edit the currently selected row."""
        if self._current_table is None:
            self.notify("Please select a table first", severity="warning")
            return

        data_view = self.query_one("#data-view", PaginatedDataTable)
        data_view.request_edit_selected()

    def action_delete_row(self) -> None:
        """Delete the currently selected row."""
        if self._current_table is None:
            self.notify("Please select a table first", severity="warning")
            return

        data_view = self.query_one("#data-view", PaginatedDataTable)
        data_view.request_delete_selected()

    def on_paginated_data_table_row_edit_requested(
        self, event: PaginatedDataTable.RowEditRequested
    ) -> None:
        """Handle edit request from the data table."""
        if self._current_table is None:
            return

        columns = self.schema.get_columns(self._current_table)
        pk_columns = self.editor.get_primary_key_columns(self._current_table)

        # Convert row data to dict
        values = {col: val for col, val in zip(event.columns, event.row_data)}

        self.push_screen(
            RowEditorScreen(
                table_name=self._current_table,
                columns=columns,
                mode=EditMode.EDIT,
                values=values,
                pk_columns=pk_columns,
            ),
            self._handle_row_editor_result,
        )

    def on_paginated_data_table_row_delete_requested(
        self, event: PaginatedDataTable.RowDeleteRequested
    ) -> None:
        """Handle delete request from the data table."""
        if self._current_table is None:
            return

        pk_columns = self.editor.get_primary_key_columns(self._current_table)
        if not pk_columns:
            self.notify("Cannot delete: table has no primary key", severity="error")
            return

        # Store data for the delete callback
        self._pending_delete = {
            "columns": event.columns,
            "row_data": event.row_data,
            "pk_columns": pk_columns,
        }

        # Build description of the row for confirmation
        pk_values = []
        for pk_col in pk_columns:
            if pk_col in event.columns:
                idx = event.columns.index(pk_col)
                pk_values.append(f"{pk_col}={event.row_data[idx]}")
        pk_desc = ", ".join(pk_values) if pk_values else "selected row"

        self.push_screen(
            ConfirmDialog(
                title="Delete Row",
                message=f"Are you sure you want to delete this row?\n\n{pk_desc}",
                confirm_label="Delete",
                cancel_label="Cancel",
            ),
            self._handle_delete_confirm,
        )

    def _handle_row_editor_result(self, result: RowEditorResult | None) -> None:
        """Handle the result from the row editor dialog."""
        if result is None or self._current_table is None:
            return

        try:
            if result.mode == EditMode.ADD:
                self.editor.insert_row(self._current_table, result.values)
                self.notify("Row added successfully", severity="information")
            else:
                pk_columns = self.editor.get_primary_key_columns(self._current_table)
                if not pk_columns:
                    self.notify("Cannot update: table has no primary key", severity="error")
                    return

                self.editor.update_row(
                    self._current_table,
                    result.values,
                    pk_columns,
                    result.original_pk_values or {},
                )
                self.notify("Row updated successfully", severity="information")

            # Refresh the data view
            self._load_table_data(self._current_table)

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    def _handle_delete_confirm(self, confirmed: bool) -> None:
        """Handle the delete confirmation result."""
        if not confirmed or self._current_table is None:
            self._pending_delete = None
            return

        pending = getattr(self, "_pending_delete", None)
        if pending is None:
            return

        try:
            pk_columns = pending["pk_columns"]
            columns = pending["columns"]
            row_data = pending["row_data"]

            # Build pk_values dict
            pk_values = {}
            for pk_col in pk_columns:
                if pk_col in columns:
                    idx = columns.index(pk_col)
                    pk_values[pk_col] = row_data[idx]

            self.editor.delete_row(self._current_table, pk_columns, pk_values)
            self.notify("Row deleted successfully", severity="information")

            # Refresh the data view
            self._load_table_data(self._current_table)

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
        finally:
            self._pending_delete = None


@click.command()
@click.argument("database", type=click.Path(exists=True, path_type=Path))
def main(database: Path) -> None:
    """SQLite Viewer - A TUI for browsing SQLite databases."""
    if not validate_sqlite_file(database):
        click.echo(f"Error: '{database}' is not a valid SQLite database file.", err=True)
        sys.exit(1)

    app = SQLiteViewerApp(database)
    app.run()


if __name__ == "__main__":
    main()
