"""Tests for data formatters."""

from rich.text import Text

from sqlite_viewer.utils.formatters import (
    format_cell_value,
    format_blob_preview,
    format_type_badge,
)


class TestFormatBlobPreview:
    """Tests for format_blob_preview function."""

    def test_small_blob(self):
        """Should format small BLOB with hex preview."""
        data = b"\x00\x01\x02\x03"
        result = format_blob_preview(data)
        assert "[BLOB:4B]" in result
        assert "00010203" in result

    def test_large_blob(self):
        """Should truncate large BLOBs."""
        data = b"\x00" * 100
        result = format_blob_preview(data, max_hex_chars=16)
        assert "[BLOB:100B]" in result
        assert "..." in result


class TestFormatCellValue:
    """Tests for format_cell_value function."""

    def test_null_value(self):
        """Should format NULL with dim italic style."""
        result = format_cell_value(None)
        assert isinstance(result, Text)
        assert str(result) == "NULL"
        assert "dim" in result.style
        assert "italic" in result.style

    def test_integer_value(self):
        """Should format integers with cyan style."""
        result = format_cell_value(42)
        assert isinstance(result, Text)
        assert str(result) == "42"
        assert "cyan" in result.style

    def test_float_value(self):
        """Should format floats with cyan style."""
        result = format_cell_value(3.14159)
        assert isinstance(result, Text)
        assert str(result) == "3.14159"
        assert "cyan" in result.style

    def test_string_value(self):
        """Should format strings without special style."""
        result = format_cell_value("Hello")
        assert isinstance(result, Text)
        assert str(result) == "Hello"

    def test_long_string_truncation(self):
        """Should truncate long strings."""
        long_text = "A" * 100
        result = format_cell_value(long_text, max_length=50)
        assert len(str(result)) == 50
        assert str(result).endswith("...")

    def test_blob_value(self):
        """Should format BLOB with yellow style."""
        result = format_cell_value(b"\x00\x01\x02")
        assert isinstance(result, Text)
        assert "[BLOB:" in str(result)
        assert "yellow" in result.style


class TestFormatTypeBadge:
    """Tests for format_type_badge function."""

    def test_integer_type(self):
        """Should format INTEGER types with cyan."""
        result = format_type_badge("INTEGER")
        assert str(result) == "INTEGER"
        assert "cyan" in result.style

    def test_text_type(self):
        """Should format TEXT types with yellow."""
        result = format_type_badge("TEXT")
        assert str(result) == "TEXT"
        assert "yellow" in result.style

    def test_blob_type(self):
        """Should format BLOB types with magenta."""
        result = format_type_badge("BLOB")
        assert str(result) == "BLOB"
        assert "magenta" in result.style

    def test_real_type(self):
        """Should format REAL types with blue."""
        result = format_type_badge("REAL")
        assert str(result) == "REAL"
        assert "blue" in result.style

    def test_varchar_type(self):
        """Should format VARCHAR types with yellow (contains CHAR)."""
        result = format_type_badge("VARCHAR(255)")
        assert str(result) == "VARCHAR(255)"
        assert "yellow" in result.style

    def test_unknown_type(self):
        """Should format unknown types with green."""
        result = format_type_badge("CUSTOM")
        assert str(result) == "CUSTOM"
        assert "green" in result.style
