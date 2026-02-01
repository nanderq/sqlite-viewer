"""Export options modal dialog."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input, RadioSet, RadioButton


class ExportDialog(ModalScreen[tuple[str, Path] | None]):
    """Modal dialog for export options."""

    DEFAULT_CSS = """
    ExportDialog {
        align: center middle;
    }

    ExportDialog > Vertical {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: thick $primary;
    }

    ExportDialog Label {
        margin: 1 0;
    }

    ExportDialog Input {
        margin: 0 0 1 0;
    }

    ExportDialog RadioSet {
        margin: 0 0 1 0;
        height: auto;
    }

    ExportDialog .buttons {
        height: 3;
        align: right middle;
    }

    ExportDialog .buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, table_name: str, default_path: Path | None = None) -> None:
        super().__init__()
        self.table_name = table_name
        self.default_path = default_path or Path.cwd()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Export table: [bold]{self.table_name}[/bold]")

            yield Label("Format:")
            with RadioSet(id="format"):
                yield RadioButton("CSV", id="csv", value=True)
                yield RadioButton("JSON", id="json")

            yield Label("Output file:")
            default_filename = f"{self.table_name}.csv"
            yield Input(
                value=str(self.default_path / default_filename),
                id="filepath",
                placeholder="Enter output file path",
            )

            with Horizontal(classes="buttons"):
                yield Button("Cancel", id="cancel", variant="default")
                yield Button("Export", id="export", variant="primary")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Update file extension when format changes."""
        filepath_input = self.query_one("#filepath", Input)
        current_path = Path(filepath_input.value)

        if event.pressed.id == "csv":
            new_path = current_path.with_suffix(".csv")
        else:
            new_path = current_path.with_suffix(".json")

        filepath_input.value = str(new_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "export":
            radio_set = self.query_one("#format", RadioSet)
            format_type = "csv" if radio_set.pressed_index == 0 else "json"
            filepath = Path(self.query_one("#filepath", Input).value)
            self.dismiss((format_type, filepath))
