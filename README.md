# SQLite Viewer

A terminal-based user interface (TUI) application for viewing and exploring SQLite databases. Built with Python and the Textual library.

## Features

- **Table Browser**: Navigate database tables via a sidebar tree with expandable column information
- **Data Viewer**: Paginated data display with keyboard navigation
- **Schema Inspector**: View column details including types, primary keys, and constraints
- **Index Viewer**: Inspect table indexes and their configurations
- **Foreign Key Viewer**: Examine foreign key relationships between tables
- **Data Export**: Export table data to CSV or JSON format

## Requirements

- Python 3.10 or higher

## Installation

### From source

Clone the repository and install in a virtual environment:

```bash
git clone https://github.com/nanderq/sqlite-viewer.git
cd sqlite-viewer
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Dependencies

The application uses:
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [Click](https://click.palletsprojects.com/) - Command-line interface

## Testing

Install development dependencies and run tests:

```bash
pip install -e ".[dev]"
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

The test suite covers:
- Database connection and file validation
- Schema introspection (tables, columns, indexes, foreign keys)
- Query pagination
- CSV/JSON export
- Data type formatters

## Usage

```bash
sqlite-viewer path/to/database.db
```

Or run as a module:

```bash
python -m sqlite_viewer path/to/database.db
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit the application |
| `e` | Export current table |
| `r` | Refresh data |
| `Tab` | Move focus to next widget |
| `Shift+Tab` | Move focus to previous widget |
| Arrow keys | Navigate tables and data |
| `Enter` | Select table |

## Project Structure

```
sqlite-viewer/
├── pyproject.toml
├── src/sqlite_viewer/
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── app.py                # Main Textual application
│   ├── app.tcss              # Stylesheet
│   ├── screens/
│   │   └── export_dialog.py  # Export modal
│   ├── widgets/
│   │   ├── table_tree.py     # Sidebar tree widget
│   │   └── data_table.py     # Paginated data table
│   ├── data/
│   │   ├── database.py       # Database connection manager
│   │   ├── schema.py         # Schema introspection
│   │   ├── query.py          # Query execution with pagination
│   │   └── exporter.py       # CSV/JSON export
│   └── utils/
│       └── formatters.py     # Data type formatters
└── tests/
```

## Data Type Display

| Type | Display Format |
|------|----------------|
| NULL | Dimmed italic "NULL" |
| BLOB | Hex preview with size indicator |
| Numbers | Right-aligned, cyan colored |
| Long text | Truncated with ellipsis |

## License

MIT
