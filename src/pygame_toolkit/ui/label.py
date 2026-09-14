"""Text on the screen without the usual ``font.render`` + ``blit`` boilerplate.

Quick example::

    score_label = pk.Label((20, 20), "Score: 0", font_size=36)

    # whenever the score changes:
    score_label.text = f"Score: {score}"

    # every frame:
    score_label.draw(screen)
"""

from __future__ import annotations

from typing import Optional, Sequence

import pygame

from ._base import Color, FontLike, Widget, resolve_font


class Label(Widget):
    """A piece of text you can place, change and draw with one line each.

    The text is only re-rendered when something actually changes, so
    it's fine to set ``label.text`` every frame.

    The label's ``rect`` always fits the text (plus ``padding``). When the
    text changes size, the label stays put at its ``anchor`` point. For
    example, a label with ``anchor="topright"`` keeps its right edge in place
    as the number grows, which is great for scores in a corner.

    Args:
        pos: Position in pixels. This is the **top-left corner** unless you
            change ``anchor``.
        text: The text to show. Non-strings (like numbers) are converted
            with ``str()``.
        font: ``None`` (default font), a system font name like ``"arial"``,
            a ``.ttf`` path, or a ``pygame.font.Font``.
        font_size: Text size in pixels. Ignored if ``font`` is a Font object.
        color: Text color.
        background: Background color behind the text, or ``None`` for
            transparent.
        padding: Empty space in pixels around the text (useful with
            ``background``).
        border_radius: Rounded corners for the background, in pixels.
        antialias: Smooth text edges. Set False for crisp pixel-art fonts.
        anchor: Which point of the label ``pos`` refers to, like
            ``"center"`` or ``"topright"``.
        visible: If False, the label isn't drawn.

    Attributes:
        text (str): The shown text. Assign to change it.
        color: Text color. Assign to change it.

    Example:
        A centered title with a background::

            title = pk.Label((400, 80), "My Cool Game", font_size=64,
                             color="white", background=(30, 30, 60),
                             padding=12, border_radius=10, anchor="center")
            title.draw(screen)
    """

    def __init__(
        self,
        pos: Sequence[float],
        text: object = "",
        *,
        font: FontLike = None,
        font_size: int = 28,
        color: Color = (255, 255, 255),
        background: Optional[Color] = None,
        padding: int = 0,
        border_radius: int = 0,
        antialias: bool = True,
        anchor: str = "topleft",
        visible: bool = True,
    ) -> None:
        super().__init__(pos, (0, 0), anchor=anchor, visible=visible)
        self.font = resolve_font(font, font_size)
        self.background = background
        self.padding = padding
        self.border_radius = border_radius
        self.antialias = antialias
        self._text = str(text)
        self._color = color
        self._surface: pygame.Surface
        self._rerender()

    @property
    def text(self) -> str:
        """The text being shown. Set it to change what the label says."""
        return self._text

    @text.setter
    def text(self, value: object) -> None:
        value = str(value)
        if value != self._text:
            self._text = value
            self._rerender()

    @property
    def color(self) -> Color:
        """The text color. Set it to recolor the label."""
        return self._color

    @color.setter
    def color(self, value: Color) -> None:
        if value != self._color:
            self._color = value
            self._rerender()

    def _rerender(self) -> None:
        self._surface = self.font.render(self._text, self.antialias, self._color)
        w, h = self._surface.get_size()
        self._resize((w + self.padding * 2, h + self.padding * 2))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the label (background first if it has one).

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        if self.background is not None:
            pygame.draw.rect(surface, self.background, self.rect,
                             border_radius=self.border_radius)
        surface.blit(self._surface, (self.rect.x + self.padding, self.rect.y + self.padding))
