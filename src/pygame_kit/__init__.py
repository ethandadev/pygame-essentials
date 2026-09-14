"""pygame-kit: handy, well-documented building blocks for pygame games.

Import it once and everything is available::

    import pygame_kit as pk

    button = pk.Button((20, 20), size=(120, 40), text="Hi")

Hover over any class in your editor, or run ``help(pk.Button)``, to see how
to use it with examples.
"""

from .ui import Button, Label, Widget, resolve_font

__version__ = "0.1.0"

__all__ = ["Button", "Label", "Widget", "resolve_font"]
