"""Bars that show how full something is: health, loading, XP, stamina, ...

Quick example::

    health = pk.ProgressBar((20, 20), size=(200, 18), smooth=True,
                            fill_color=(220, 60, 60), trail_color=(255, 220, 120))

    # whenever the player gets hurt:
    health.set_from(player.hp, player.max_hp)

    # every frame:
    health.update(dt)
    health.draw(screen)
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence, Union

import pygame

from ._base import Color, FontLike, Widget, resolve_font


class ProgressBar(Widget):
    """A horizontal bar that fills up from left to right.

    ``value`` is a number from **0.0 (empty)** to **1.0 (full)**. If your
    numbers are like "37 out of 50", use :meth:`set_from` and it does the
    math for you.

    Two optional effects make it feel nice:

    * ``smooth=True``: the bar glides to the new value instead of jumping.
    * ``trail_color``: when the value **drops**, the lost part stays visible
      in this color for a moment, then shrinks away. This is the classic
      "damage chip" effect from fighting games. It needs ``update(dt)``.

    Args:
        pos: Position in pixels. This is the **top-left corner** unless you
            change ``anchor``.
        size: ``(width, height)`` in pixels.
        value: Starting fill, from 0.0 to 1.0.
        background: Color of the empty part.
        fill_color: Color of the filled part. Can also be a function
            ``fill_color(value) -> color``, for example to turn red when low.
        trail_color: Color of the "just lost" part, or ``None`` for no trail.
        border_color: Outline color, or ``None`` for no outline.
        border_width: Outline thickness in pixels.
        border_radius: How rounded the corners are. ``None`` = fully round
            ends.
        smooth: If True, the fill glides toward ``value`` (needs
            ``update(dt)``).
        speed: How fast smooth filling and the trail move, in "full bars per
            second". 2.0 means going from empty to full takes half a second.
        show_text: If True, draws the percentage, like ``"75%"``, in the middle.
            To show something else, set ``text_format``.
        text_format: A function ``text_format(value) -> str`` for the
            middle text, for example ``lambda v: f"{int(v * 50)}/50 HP"``.
            Turns on ``show_text``.
        font: Font for the text.
        font_size: Text size in pixels.
        text_color: Text color.
        anchor: Which point of the bar ``pos`` refers to.
        visible: If False, it's not drawn.

    Attributes:
        value (float): The target fill from 0.0 to 1.0 (always clamped).
        shown_value (float): What's currently drawn. This differs from
            ``value`` while smoothly animating.

    Example:
        A health bar that turns red when low::

            def hp_color(v):
                return (60, 200, 90) if v > 0.3 else (230, 60, 60)

            hp = pk.ProgressBar((20, 20), size=(220, 20), fill_color=hp_color,
                                text_format=lambda v: f"{round(v * 100)} HP")
    """

    def __init__(
        self,
        pos: Sequence[float],
        size: Sequence[float] = (200, 20),
        *,
        value: float = 1.0,
        background: Color = (60, 60, 60),
        fill_color: Union[Color, Callable[[float], Color]] = (60, 200, 90),
        trail_color: Optional[Color] = None,
        border_color: Optional[Color] = None,
        border_width: int = 2,
        border_radius: Optional[int] = None,
        smooth: bool = False,
        speed: float = 2.0,
        show_text: bool = False,
        text_format: Optional[Callable[[float], str]] = None,
        font: FontLike = None,
        font_size: int = 22,
        text_color: Color = (255, 255, 255),
        anchor: str = "topleft",
        visible: bool = True,
    ) -> None:
        super().__init__(pos, size, anchor=anchor, visible=visible)
        self.background = background
        self.fill_color = fill_color
        self.trail_color = trail_color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.smooth = smooth
        self.speed = speed
        self.text_format = text_format
        self.show_text = show_text or text_format is not None
        self.font = resolve_font(font, font_size)
        self.text_color = text_color
        self._value = self._clamp(value)
        self.shown_value = self._value
        self._trail = self._value
        self._trail_delay = 0.0

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    @property
    def value(self) -> float:
        """The target fill, from 0.0 (empty) to 1.0 (full)."""
        return self._value

    @value.setter
    def value(self, new: float) -> None:
        new = self._clamp(new)
        if new < self._value and self.trail_color is not None:
            self._trail = max(self._trail, self.shown_value)
            self._trail_delay = 0.35
        self._value = new
        if not self.smooth:
            self.shown_value = new
        if self.trail_color is None:
            self._trail = new

    def set_from(self, current: float, maximum: float) -> None:
        """Set the fill from "current out of maximum", like ``set_from(hp, max_hp)``.

        Args:
            current: The current amount, like 37.
            maximum: The full amount, like 50. If this is 0 or less, the bar
                becomes empty.
        """
        self.value = current / maximum if maximum > 0 else 0.0

    def update(self, dt: float = 0.0) -> None:
        """Animate smooth filling and the damage trail. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        step = self.speed * dt
        if self.shown_value < self._value:
            self.shown_value = min(self._value, self.shown_value + step)
        elif self.shown_value > self._value:
            self.shown_value = max(self._value, self.shown_value - step)
        if self._trail_delay > 0:
            self._trail_delay -= dt
        elif self._trail > self.shown_value:
            self._trail = max(self.shown_value, self._trail - step)
        if self._trail < self.shown_value:
            self._trail = self.shown_value

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the background, trail, fill, text and outline.

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        radius = self.rect.height // 2 if self.border_radius is None else self.border_radius
        pygame.draw.rect(surface, self.background, self.rect, border_radius=radius)

        def bar(fraction: float, color: Color) -> None:
            w = round(self.rect.width * fraction)
            if w > 0:
                pygame.draw.rect(surface, color, (self.rect.x, self.rect.y, w, self.rect.height),
                                 border_radius=radius)

        if self.trail_color is not None and self._trail > self.shown_value:
            bar(self._trail, self.trail_color)
        fill = self.fill_color(self.shown_value) if callable(self.fill_color) else self.fill_color
        bar(self.shown_value, fill)

        if self.show_text:
            label = self.text_format(self._value) if self.text_format else f"{round(self._value * 100)}%"
            text = self.font.render(label, True, self.text_color)
            surface.blit(text, text.get_rect(center=self.rect.center))
        if self.border_color is not None and self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, self.rect, self.border_width,
                             border_radius=radius)
