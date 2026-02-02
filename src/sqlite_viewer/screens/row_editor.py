"""Row editor modal screen."""

from enum import Enum
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input, Static, Checkbox

from sqlite_viewer.data.schema import ColumnInfo


class EditMode(Enum):
    """Mode for the row editor."""

    ADD = "add"
    EDIT = "edit"


class RowEditorResult:
    """Result from the row editor dialog."""

    def __init__(
        self,
        mode: EditMode,
        values: dict[str, Any],
        original_pk_values: dict[str, Any] | None = None,
    ) -> None:
        self.mode = mode
        self.values = values
        self.original_pk_values = original_pk_values


class FieldEditor(Vertical):
    """Editor widget for a single field."""

    DEFAULT_CSS = """
    FieldEditor {
        height: auto;
        margin-bottom: 1;
    }
    FieldEditor .field-label {
        height: 1;
        margin-bottom: 0;
    }
    FieldEditor .field-info {
        height: 1;
        color: $text-muted;
        text-style: italic;
    }
    FieldEditor Input {
        margin-top: 0;
    }
    FieldEditor .null-checkbox {
        margin-top: 1;
    }
    """

    def __init__(
        self,
        column: ColumnInfo,
        value: Any = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.column = column
        self.initial_value = value
        self._is_null = value is None

    def compose(self) -> ComposeResult:
        # Column name and type info
        pk_marker = " 🔑" if self.column.primary_key else ""
        nn_marker = " *" if self.column.not_null else ""
        yield Label(
            f"[bold]{self.column.name}[/bold]{pk_marker}{nn_marker}",
            classes="field-label",
        )

        type_info = f"Type: {self.column.type}"
        if self.column.default_value is not None:
            type_info += f" | Default: {self.column.default_value}"
        yield Static(type_info, classes="field-info")

        # Value input
        display_value = "" if self.initial_value is None else str(self.initial_value)
        if isinstance(self.initial_value, bytes):
            display_value = f"[BLOB:{len(self.initial_value)}B]"

        yield Input(
            value=display_value,
            placeholder="NULL" if not self.column.not_null else "Enter value",
            id=f"input-{self.column.name}",
            disabled=self._is_null,
        )

        # NULL checkbox (only if column allows NULL)
        if not self.column.not_null:
            yield Checkbox(
                "Set as NULL",
                value=self._is_null,
                id=f"null-{self.column.name}",
                classes="null-checkbox",
            )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle NULL checkbox toggle."""
        self._is_null = event.value
        input_widget = self.query_one(f"#input-{self.column.name}", Input)
        input_widget.disabled = self._is_null
        if self._is_null:
            input_widget.value = ""

    def get_value(self) -> Any:
        """Get the current field value."""
        if self._is_null:
            return None

        input_widget = self.query_one(f"#input-{self.column.name}", Input)
        value = input_widget.value

        # Handle empty string
        if value == "" and not self.column.not_null:
            return None

        # Handle BLOB (keep original if unchanged)
        if isinstance(self.initial_value, bytes):
            if value == f"[BLOB:{len(self.initial_value)}B]":
                return self.initial_value

        # Type conversion based on column type
        col_type = self.column.type.upper()
        if "INT" in col_type:
            try:
                return int(value)
            except ValueError:
                return value
        elif "REAL" in col_type or "FLOAT" in col_type or "DOUBLE" in col_type:
            try:
                return float(value)
            except ValueError:
                return value

        return value


class RowEditorScreen(ModalScreen[RowEditorResult | None]):
    """Modal screen for editing a table row."""

    DEFAULT_CSS = """
    RowEditorScreen {
        align: center middle;
    }

    RowEditorScreen > Vertical {
        width: 80;
        max-width: 90%;
        height: auto;
        max-height: 90%;
        padding: 1 2;
        background: $surface;
        border: thick $primary;
    }

    RowEditorScreen .title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }

    RowEditorScreen .fields-container {
        height: auto;
        max-height: 60vh;
        padding: 0 1;
    }

    RowEditorScreen .buttons {
        height: 3;
        align: right middle;
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary;
    }

    RowEditorScreen .buttons Button {
        margin: 0 1;
    }

    RowEditorScreen .error-message {
        color: $error;
        height: auto;
        padding: 1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        table_name: str,
        columns: list[ColumnInfo],
        mode: EditMode = EditMode.ADD,
        values: dict[str, Any] | None = None,
        pk_columns: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.table_name = table_name
        self.columns = columns
        self.mode = mode
        self.values = values or {}
        self.pk_columns = pk_columns or []
        self._original_pk_values: dict[str, Any] = {}

        # Store original PK values for edit mode
        if mode == EditMode.EDIT:
            for pk_col in self.pk_columns:
                if pk_col in self.values:
                    self._original_pk_values[pk_col] = self.values[pk_col]

    def compose(self) -> ComposeResult:
        with Vertical():
            # Title
            mode_text = "Add New Row" if self.mode == EditMode.ADD else "Edit Row"
            yield Static(
                f"{mode_text} - [cyan]{self.table_name}[/cyan]",
                classes="title",
            )

            # Fields container (scrollable)
            with VerticalScroll(classes="fields-container"):
                for column in self.columns:
                    value = self.values.get(column.name)
                    yield FieldEditor(
                        column=column,
                        value=value,
                        id=f"field-{column.name}",
                    )

            # Error message placeholder
            yield Static("", id="error-message", classes="error-message")

            # Buttons
            with Horizontal(classes="buttons"):
                yield Button("Cancel", id="cancel", variant="default")
                save_label = "Add Row" if self.mode == EditMode.ADD else "Save Changes"
                yield Button(save_label, id="save", variant="primary")

    def action_cancel(self) -> None:
        """Cancel editing."""
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "save":
            self._save()

    def _save(self) -> None:
        """Validate and save the row."""
        values: dict[str, Any] = {}
        errors: list[str] = []

        for column in self.columns:
            field = self.query_one(f"#field-{column.name}", FieldEditor)
            value = field.get_value()

            # Validate NOT NULL constraint
            if column.not_null and value is None:
                errors.append(f"'{column.name}' cannot be NULL")
                continue

            values[column.name] = value

        if errors:
            error_widget = self.query_one("#error-message", Static)
            error_widget.update("\n".join(errors))
            return

        result = RowEditorResult(
            mode=self.mode,
            values=values,
            original_pk_values=self._original_pk_values if self.mode == EditMode.EDIT else None,
        )
        self.dismiss(result)
