# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Test Commands

```bash
# Install in development mode
pip install -e .

# Install with test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a single test file
pytest tests/test_schema.py

# Run a specific test
pytest tests/test_schema.py::TestSchemaInspector::test_get_tables

# Run the application
sqlite-viewer path/to/database.db
python -m sqlite_viewer path/to/database.db
```

## Architecture

This is a TUI application for viewing SQLite databases, built with Textual.

### Layer Structure

**Data Layer** (`src/sqlite_viewer/data/`):
- `DatabaseConnection` - Context manager wrapping sqlite3, provides cursor access
- `SchemaInspector` - Uses PRAGMA statements to introspect tables, columns, indexes, foreign keys
- `PaginatedQuery` - Handles LIMIT/OFFSET pagination with cached row counts
- `Exporter` - Streaming CSV/JSON export to avoid memory issues with large tables

**UI Layer** (`src/sqlite_viewer/widgets/`):
- `TableTree` - Extends Textual's Tree widget, posts `TableSelected` messages when user selects a table
- `PaginatedDataTable` - Extends Vertical container with DataTable and pagination controls

**Application** (`src/sqlite_viewer/app.py`):
- `SQLiteViewerApp` - Main Textual App, handles message routing between widgets
- Listens for `TableTree.TableSelected` messages via `on_table_tree_table_selected` handler
- Manages four tabs: Data, Schema, Indexes, Foreign Keys

### Message Flow

1. User clicks table in `TableTree`
2. `TableTree` posts `TableSelected` message
3. `SQLiteViewerApp.on_table_tree_table_selected` receives message
4. App creates `PaginatedQuery` and passes to `PaginatedDataTable`
5. App updates schema/index/FK tabs via `SchemaInspector`

### Data Type Handling

The `utils/formatters.py` module handles display formatting:
- NULL values: dimmed italic text
- BLOB values: hex preview with size (e.g., `[BLOB:1234B] 0a1b2c...`)
- Numbers: cyan colored
- Long text: truncated with ellipsis
