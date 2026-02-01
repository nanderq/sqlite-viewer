"""Main Textual application for SQLite Viewer."""

import sys
from pathlib import Path

import click
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, TabbedContent, TabPane, Static, DataTable

from sqlite_viewer.data.database import DatabaseConnection, validate_sqlite_file
from sqlite_viewer.data.schema import SchemaInspector
from sqlite_viewer.data.query import PaginatedQuery
from sqlite_viewer.data.exporter import Exporter
from sqlite_viewer.widgets.table_tree import TableTree
from sqlite_viewer.widgets.data_table import PaginatedDataTable
from sqlite_viewer.screens.export_dialog import ExportDialog


class SQLiteViewerApp(App):
    """A TUI application for viewing SQLite databases."""

    TITLE = "SQLite Viewer"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("e", "export", "Export"),
        Binding("r", "refresh", "Refresh"),
        Binding("tab", "focus_next", "Focus Next"),
        Binding("shift+tab", "focus_previous", "Focus Prev"),
    ]

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self.db = DatabaseConnection(db_path)
        self.schema = SchemaInspector(self.db)
        self.exporter = Exporter(self.db)
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
