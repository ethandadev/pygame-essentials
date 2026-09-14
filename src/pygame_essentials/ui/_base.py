"""Shared building blocks for every pygame-essentials UI widget.

You normally don't use this module directly. It holds:

* :class:`Widget`: the base class every widget (Button, Slider, ...) builds on.
* :func:`resolve_font`: turns "a font name, a file path, a Font, or None"
  into a real ``pygame.font.Font`` and caches it so fonts aren't reloaded
  every frame.

If you want to make **your own** widget, subclass :class:`Widget`::

    from pygame_essentials.ui import Widget

    class Star(Widget):
        def draw(self, surface):
            if self.visible:
                pygame.draw.circle(surface, "gold", self.rect.center, self.rect.width // 2)
"""

from __future__ import annotations

import os
from typing import Optional, Sequence, Tuple, Union

import pygame

Color = Union[pygame.Color, str, Tuple[int, int, int], Tuple[int, int, int, int]]
"""Anything pygame accepts as a color: ``(255, 0, 0)``, ``(255, 0, 0, 128)``, ``"red"``, or ``pygame.Color``."""

FontLike = Union[pygame.font.Font, str, "os.PathLike[str]", None]
"""A ``pygame.font.Font``, a path to a ``.ttf``/``.otf`` file, a system font name like ``"arial"``, or ``None`` for pygame's default font."""

_ANCHORS = (
    "topleft", "midtop", "topright",
    "midleft", "center", "midright",
    "bottomleft", "midbottom", "bottomright",
)

_font_cache: dict = {}


def resolve_font(font: FontLike = None, size: int = 28) -> pygame.font.Font:
    """Get a ready-to-use ``pygame.font.Font``, loading it only once.

    Loading fonts is slow, so this remembers every font it has loaded. Calling
    it again with the same arguments gives back the same Font object.

    Args:
        font: What font to use. Can be:

            * ``None``: pygame's built-in default font.
            * A path ending in ``.ttf`` or ``.otf``, like ``"assets/pixel.ttf"``
              (a ``pathlib.Path`` works too).
            * A system font name, like ``"arial"`` or ``"comicsansms"``.
            * An existing ``pygame.font.Font``, which is returned unchanged
              (``size`` is ignored).
        size: Font size in pixels. Ignored if ``font`` is already a Font.

    Returns:
        A ``pygame.font.Font`` you can call ``.render()`` on.

    Note:
        ``pygame.font.init()`` is called for you if needed, so this works even
        if you forgot ``pygame.init()``.
    """
    if isinstance(font, pygame.font.Font):
        return font
    if not pygame.font.get_init():
        pygame.font.init()
        _font_cache.clear()  # fonts loaded before pygame.quit() can't be used any more
    if font is not None:
        font = os.fspath(font)
    key = (font, size)
    cached = _font_cache.get(key)
    if cached is None:
        if font is None:
            cached = pygame.font.Font(None, size)
        elif font.lower().endswith((".ttf", ".otf")):
            cached = pygame.font.Font(font, size)
        else:
            cached = pygame.font.SysFont(font, size)
        _font_cache[key] = cached
    return cached


class Widget:
    """Base class for all UI widgets: a rectangle that can react to events and draw itself.

    Every widget in pygame-essentials follows the same three-step pattern, so once you
    know one you know them all:

    1. ``handle_event(event)``: call for **every** event inside your
       ``for event in pygame.event.get()`` loop.
    2. ``update(dt)``: call **once per frame**. ``dt`` is the time since the
       last frame in **seconds** (for example ``clock.tick(60) / 1000``).
    3. ``draw(surface)``: call once per frame after you clear the screen.

    Args:
        pos: Where to place the widget, in pixels. By default this is the
            **top-left corner**. Change that with ``anchor``. Decimal
            positions (like a ``Vector2`` or ``FRect.center``) are rounded.
        size: ``(width, height)`` in pixels.
        anchor: Which point of the widget ``pos`` refers to. One of
            ``"topleft"`` (default), ``"center"``, ``"midtop"``,
            ``"topright"``, ``"midleft"``, ``"midright"``, ``"bottomleft"``,
            ``"midbottom"``, ``"bottomright"``.
            Example: ``anchor="center"`` with ``pos=(400, 300)`` centers the
            widget on an 800x600 screen.
        visible: If False, the widget isn't drawn and ignores events.
        enabled: If False, the widget is drawn (usually grayed out) but
            ignores clicks and typing.

    Attributes:
        rect (pygame.Rect): The widget's position and size. You can move a
            widget by changing it, for example ``widget.rect.x += 10``.
        visible (bool): See ``visible`` above.
        enabled (bool): See ``enabled`` above.
        hovered (bool): True while the mouse is over the widget.
        pressed (bool): True while the left mouse button is held down after
            pressing on the widget.

    Raises:
        ValueError: If ``anchor`` isn't one of the names listed above.
    """

    def __init__(
        self,
        pos: Sequence[float],
        size: Sequence[float],
        *,
        anchor: str = "topleft",
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        if anchor not in _ANCHORS:
            raise ValueError(
                f"anchor must be one of {', '.join(_ANCHORS)} (got {anchor!r})"
            )
        self.rect = pygame.Rect(0, 0, round(size[0]), round(size[1]))
        setattr(self.rect, anchor, (round(pos[0]), round(pos[1])))
        self.anchor = anchor
        self.visible = visible
        self.enabled = enabled
        self.hovered = False
        self.pressed = False

    # ------------------------------------------------------------------ helpers
    @property
    def active(self) -> bool:
        """True if the widget is both visible and enabled, so it should react to input."""
        return self.visible and self.enabled

    def _resize(self, size: Sequence[float]) -> None:
        """Change the size while keeping the anchor point in place."""
        point = getattr(self.rect, self.anchor)
        self.rect.size = (round(size[0]), round(size[1]))
        setattr(self.rect, self.anchor, point)

    def _track_click(self, event: pygame.event.Event) -> bool:
        """Update ``hovered``/``pressed`` from a mouse event.

        Returns:
            True exactly when a full click finished on this widget: the left
            button was pressed **and** released while over it. This is how
            real buttons in apps work, and it means holding the mouse down
            counts as one click, not one per frame.
        """
        if not self.active:
            self.hovered = self.pressed = False
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hovered = self.rect.collidepoint(event.pos)
            self.pressed = self.hovered
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.hovered = self.rect.collidepoint(event.pos)
            clicked = self.pressed and self.hovered
            self.pressed = False
            return clicked
        return False

    # ------------------------------------------------------------ the 3 steps
    def handle_event(self, event: pygame.event.Event) -> bool:
        """React to one pygame event. Call this for every event, every frame.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if the widget "used" the event (for example, a click landed
            on it). You can use this to stop the same click from also
            reaching your game world.
        """
        return False

    def update(self, dt: float = 0.0) -> None:
        """Advance animations. Call once per frame.

        Args:
            dt: Seconds since the last frame. Use ``clock.tick(60) / 1000``.
        """

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the widget onto ``surface`` (usually your screen)."""

    def __repr__(self) -> str:
        return f"<{type(self).__name__} rect={tuple(self.rect)}>"
