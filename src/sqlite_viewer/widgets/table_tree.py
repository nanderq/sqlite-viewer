"""Sidebar tree widget showing database tables and columns."""

from textual.widgets import Tree
from textual.message import Message

from sqlite_viewer.data.schema import SchemaInspector, ColumnInfo


class TableTree(Tree):
    """Tree widget displaying database tables and their columns."""

    class TableSelected(Message):
        """Message sent when a table is selected."""

        def __init__(self, table_name: str) -> None:
            self.table_name = table_name
            super().__init__()

    def __init__(self, schema: SchemaInspector, **kwargs) -> None:
        super().__init__("Tables", **kwargs)
        self.schema = schema
        self._tables: list[str] = []

    def on_mount(self) -> None:
        """Load tables when mounted."""
        self.load_tables()

    def load_tables(self) -> None:
        """Load all tables from the database."""
        self.clear()
        self._tables = self.schema.get_tables()

        for table_name in self._tables:
            table_node = self.root.add(table_name, data={"type": "table", "name": table_name})
            # Add columns as children
            columns = self.schema.get_columns(table_name)
            for col in columns:
                col_label = self._format_column_label(col)
                table_node.add_leaf(col_label, data={"type": "column", "column": col})

        self.root.expand()

    def _format_column_label(self, col: ColumnInfo) -> str:
        """Format a column label for display."""
        pk_marker = " 🔑" if col.primary_key else ""
        nn_marker = " *" if col.not_null else ""
        return f"{col.name} ({col.type}){pk_marker}{nn_marker}"

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection."""
        node = event.node
        if node.data and node.data.get("type") == "table":
            self.post_message(self.TableSelected(node.data["name"]))
        elif node.data and node.data.get("type") == "column":
            # When clicking a column, select the parent table
            parent = node.parent
            if parent and parent.data and parent.data.get("type") == "table":
                self.post_message(self.TableSelected(parent.data["name"]))
