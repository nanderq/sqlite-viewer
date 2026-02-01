"""Data type formatters for display."""

from typing import Any

from rich.text import Text


def format_blob_preview(data: bytes, max_hex_chars: int = 16) -> str:
    """Format a BLOB value as a hex preview."""
    hex_preview = data[:max_hex_chars // 2].hex()
    return f"[BLOB:{len(data)}B] {hex_preview}..."


def format_cell_value(value: Any, max_length: int = 50) -> Text:
    """Format a cell value for display with rich text styling."""
    if value is None:
        return Text("NULL", style="dim italic")

    if isinstance(value, bytes):
        return Text(format_blob_preview(value), style="yellow")

    if isinstance(value, (int, float)):
        text = str(value)
        return Text(text, style="cyan")

    # String value
    text = str(value)
    if len(text) > max_length:
        text = text[: max_length - 3] + "..."
    return Text(text)


def format_type_badge(type_name: str) -> Text:
    """Format a column type as a styled badge."""
    type_upper = type_name.upper()
    style = "green"
    if "INT" in type_upper:
        style = "cyan"
    elif "TEXT" in type_upper or "CHAR" in type_upper:
        style = "yellow"
    elif "BLOB" in type_upper:
        style = "magenta"
    elif "REAL" in type_upper or "FLOAT" in type_upper or "DOUBLE" in type_upper:
        style = "blue"
    return Text(type_name, style=style)
