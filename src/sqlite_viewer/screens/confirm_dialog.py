"""Confirmation dialog for destructive actions."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen[bool]):
    """Modal dialog for confirming destructive actions."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Vertical {
        width: 50;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: thick $error;
    }

    ConfirmDialog .title {
        text-align: center;
        text-style: bold;
        color: $error;
        padding-bottom: 1;
    }

    ConfirmDialog .message {
        text-align: center;
        padding: 1 0;
    }

    ConfirmDialog .buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    ConfirmDialog .buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_label: str = "Confirm",
        cancel_label: str = "Cancel",
    ) -> None:
        super().__init__()
        self.title_text = title
        self.message_text = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.title_text, classes="title")
            yield Static(self.message_text, classes="message")
            with Horizontal(classes="buttons"):
                yield Button(self.cancel_label, id="cancel", variant="default")
                yield Button(self.confirm_label, id="confirm", variant="error")

    def action_cancel(self) -> None:
        """Cancel the action."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.dismiss(False)
        elif event.button.id == "confirm":
            self.dismiss(True)
