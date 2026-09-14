"""UI widgets: buttons, labels, text boxes, sliders, checkboxes, dropdowns and progress bars.

Every widget uses the same three calls:

* ``widget.handle_event(event)``: for each event in your event loop
* ``widget.update(dt)``: once per frame (``dt`` in seconds)
* ``widget.draw(screen)``: once per frame, after clearing the screen
"""

from ._base import Widget, resolve_font
from .button import Button
from .checkbox import Checkbox, Toggle
from .dropdown import Dropdown
from .label import Label
from .progress_bar import ProgressBar
from .slider import Slider
from .text_input import TextInput

__all__ = [
    "Widget", "resolve_font",
    "Button", "Label", "TextInput", "Slider",
    "Checkbox", "Toggle", "Dropdown", "ProgressBar",
]
