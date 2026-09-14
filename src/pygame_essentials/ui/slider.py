"""A draggable slider for picking a number (volume, speed, brightness, ...).

Quick example::

    volume = pk.Slider((50, 50), size=(200, 8), value=0.8,
                       on_change=lambda v: pygame.mixer.music.set_volume(v))

    # in your loop:
    for event in pygame.event.get():
        volume.handle_event(event)
    volume.draw(screen)
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import pygame

from ._base import Color, Widget


class Slider(Widget):
    """A horizontal slider: drag the handle, or click anywhere on the track, to change the value.

    Args:
        pos: Position of the **track** in pixels. This is the **top-left
            corner** unless you change ``anchor``.
        size: ``(width, height)`` of the track in pixels. A thin track like
            ``(200, 8)`` looks nice, and the handle sticks out above and below.
        min_value: The value when the handle is all the way left.
        max_value: The value when the handle is all the way right.
        value: Starting value. Defaults to ``min_value``. Values outside the
            range are clamped (pushed back inside).
        step: If given, the value snaps to multiples of this, counting from
            ``min_value``. For example ``step=1`` gives whole numbers and
            ``step=0.25`` gives quarter steps. ``None`` = smooth.
        track_color: Color of the empty part of the track.
        fill_color: Color of the part left of the handle.
        handle_color: Color of the round handle.
        handle_hover_color: Handle color while hovering or dragging.
        handle_radius: Handle size in pixels. Defaults to a size that fits
            the track height.
        on_change: Function called as ``on_change(value)`` whenever the value
            changes.
        anchor: Which point of the track ``pos`` refers to.
        visible: If False, the slider is hidden and ignores input.
        enabled: If False, the slider can't be dragged.

    Attributes:
        value (float): The current value. You can set it from code. That is
            clamped and snapped too, but does **not** call ``on_change``.
        dragging (bool): True while the player is dragging the handle.

    Raises:
        ValueError: If ``max_value`` isn't bigger than ``min_value``, or
            ``step`` isn't positive.

    Example:
        A whole-number difficulty picker with a label::

            difficulty = pk.Slider((50, 100), size=(200, 8),
                                   min_value=1, max_value=5, step=1, value=3)
            label = pk.Label((270, 92), "")
            ...
            label.text = f"Difficulty: {int(difficulty.value)}"
    """

    def __init__(
        self,
        pos: Sequence[float],
        size: Sequence[float] = (200, 8),
        *,
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: Optional[float] = None,
        step: Optional[float] = None,
        track_color: Color = (200, 200, 200),
        fill_color: Color = (60, 130, 240),
        handle_color: Color = (255, 255, 255),
        handle_hover_color: Color = (230, 240, 255),
        handle_radius: Optional[int] = None,
        on_change: Optional[Callable[[float], None]] = None,
        anchor: str = "topleft",
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        if max_value <= min_value:
            raise ValueError(
                f"max_value ({max_value}) must be bigger than min_value ({min_value})"
            )
        if step is not None and step <= 0:
            raise ValueError(f"step must be positive (got {step})")
        super().__init__(pos, size, anchor=anchor, visible=visible, enabled=enabled)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.track_color = track_color
        self.fill_color = fill_color
        self.handle_color = handle_color
        self.handle_hover_color = handle_hover_color
        self.handle_radius = handle_radius or max(8, self.rect.height)
        self.on_change = on_change
        self.dragging = False
        self._value = self._clean(min_value if value is None else value)

    # ------------------------------------------------------------------ value
    @property
    def value(self) -> float:
        """The current value, always between ``min_value`` and ``max_value``."""
        return self._value

    @value.setter
    def value(self, new: float) -> None:
        self._value = self._clean(new)

    @property
    def fraction(self) -> float:
        """How far along the slider is, from 0.0 (left) to 1.0 (right)."""
        return (self._value - self.min_value) / (self.max_value - self.min_value)

    def _clean(self, v: float) -> float:
        v = max(self.min_value, min(self.max_value, v))
        if self.step is not None:
            steps = round((v - self.min_value) / self.step)
            v = self.min_value + steps * self.step
            v = max(self.min_value, min(self.max_value, v))
            v = round(v, 10)  # hide float noise like 0.30000000000000004
        return v

    def _handle_pos(self) -> tuple:
        return (round(self.rect.x + self.fraction * self.rect.width), self.rect.centery)

    def _hit_area(self) -> pygame.Rect:
        grow = self.handle_radius * 2
        return self.rect.inflate(grow, max(0, grow - self.rect.height))

    def _set_from_x(self, x: int) -> None:
        frac = (x - self.rect.x) / max(1, self.rect.width)
        new = self._clean(self.min_value + frac * (self.max_value - self.min_value))
        if new != self._value:
            self._value = new
            if self.on_change is not None:
                self.on_change(new)

    # ------------------------------------------------------------------ input
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle dragging and clicking on the track. Call for every event.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if the slider used the event.
        """
        if not self.active:
            self.dragging = self.hovered = False
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hit_area().collidepoint(event.pos):
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self._hit_area().collidepoint(event.pos)
            if self.dragging:
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        return False

    # ---------------------------------------------------------------- drawing
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the track, the filled part and the handle.

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        radius = self.rect.height // 2
        pygame.draw.rect(surface, self.track_color, self.rect, border_radius=radius)
        hx, hy = self._handle_pos()
        filled = pygame.Rect(self.rect.x, self.rect.y, hx - self.rect.x, self.rect.height)
        if filled.width > 0:
            pygame.draw.rect(surface, self.fill_color, filled, border_radius=radius)
        color = self.handle_hover_color if (self.hovered or self.dragging) else self.handle_color
        if not self.enabled:
            color = (170, 170, 170)
        pygame.draw.circle(surface, (150, 150, 150), (hx, hy + 1), self.handle_radius)
        pygame.draw.circle(surface, color, (hx, hy), self.handle_radius - 1)
        pygame.draw.circle(surface, self.fill_color, (hx, hy), self.handle_radius - 1, 2)
