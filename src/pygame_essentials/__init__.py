"""pygame-essentials: handy, well-documented building blocks for pygame games.

Import it once and everything is available::

    import pygame_essentials as pk

    button = pk.Button((20, 20), size=(120, 40), text="Hi")

Hover over any class in your editor, or run ``help(pk.Button)``, to see how
to use it with examples.
"""

from .ui import (
    Button, Checkbox, Dropdown, Label, ProgressBar, Slider, TextInput, Toggle,
    Widget, resolve_font,
)
from .animation import Animation, AnimationSet, Spritesheet
from .camera import Camera
from .debug import DebugOverlay
from .particles import Particle, ParticleEmitter
from .save import SaveData, default_save_folder
from .timing import Cooldown, Timer

__version__ = "0.1.0"

__all__ = [
    # UI
    "Widget", "resolve_font",
    "Button", "Label", "TextInput", "Slider",
    "Checkbox", "Toggle", "Dropdown", "ProgressBar",
    # Time
    "Timer", "Cooldown",
    # Graphics
    "Spritesheet", "Animation", "AnimationSet", "Camera", "ParticleEmitter", "Particle",
    # Extras
    "SaveData", "default_save_folder", "DebugOverlay",
]
