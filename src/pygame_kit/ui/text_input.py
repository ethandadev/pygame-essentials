"""A text box the player can click and type into (names, chat, seeds, ...).

Quick example::

    name_box = pk.TextInput((300, 250), size=(200, 40),
                            placeholder="Your name", max_length=12,
                            on_submit=lambda text: print("Hi", text))

    # in your loop:
    for event in pygame.event.get():
        name_box.handle_event(event)
    name_box.update(dt)      # makes the cursor blink
    name_box.draw(screen)

Tip:
    Call ``pygame.key.set_repeat(400, 35)`` once after ``pygame.init()`` so
    holding Backspace or the arrow keys repeats, like in normal apps.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import pygame

from ._base import Color, FontLike, Widget, resolve_font


class TextInput(Widget):
    """A one-line text box with a blinking cursor.

    Click the box to start typing, and click anywhere else to stop.
    Supported keys:

    * Letters, numbers, and symbols (anything your keyboard types)
    * **Backspace** / **Delete**: erase before / after the cursor
    * **Left** / **Right**: move the cursor. **Home** / **End**: jump to the
      start / end.
    * **Enter**: calls ``on_submit(text)``
    * **Escape**: stop typing (unfocus)

    If the text is wider than the box, it scrolls so the cursor stays
    visible.

    Args:
        pos: Position in pixels. This is the **top-left corner** unless you
            change ``anchor``.
        size: ``(width, height)`` of the box in pixels.
        text: Text the box starts with.
        placeholder: Gray hint text shown while the box is empty, like
            ``"Enter your name"``.
        font: ``None`` (default font), a system font name, a ``.ttf`` path,
            or a ``pygame.font.Font``.
        font_size: Text size in pixels.
        text_color: Color of typed text.
        placeholder_color: Color of the placeholder hint.
        background: Box background color.
        border_color: Outline color when not typing.
        focus_border_color: Outline color while typing (focused).
        border_width: Outline thickness in pixels.
        border_radius: How rounded the corners are, in pixels.
        padding: Space in pixels between the box edge and the text.
        max_length: Maximum number of characters, or ``None`` for no limit.
        allowed_chars: If given, only these characters can be typed. For
            example ``"0123456789"`` for a number-only box.
        clear_on_submit: If True, the box empties itself after Enter (handy
            for chat boxes).
        on_submit: Function called as ``on_submit(text)`` when Enter is
            pressed.
        on_change: Function called as ``on_change(text)`` whenever the
            player changes the text.
        anchor: Which point of the box ``pos`` refers to.
        visible: If False, the box is hidden and ignores input.
        enabled: If False, the box can't be focused or typed in.

    Attributes:
        text (str): The current text. You can also set it yourself (that
            doesn't call ``on_change``).
        focused (bool): True while the box is receiving typing. Set it to True
            to focus the box from code.
        cursor (int): Cursor position as a character index (0 = before the
            first character).

    Raises:
        ValueError: If ``max_length`` is negative.

    Example:
        A seed box that only accepts digits::

            seed_box = pk.TextInput((20, 20), size=(160, 36),
                                    placeholder="Seed", allowed_chars="0123456789",
                                    max_length=9)
            ...
            seed = int(seed_box.text or 0)
    """

    CURSOR_BLINK_SECONDS = 0.5

    def __init__(
        self,
        pos: Sequence[float],
        size: Sequence[float] = (240, 40),
        text: str = "",
        *,
        placeholder: str = "",
        font: FontLike = None,
        font_size: int = 28,
        text_color: Color = (20, 20, 20),
        placeholder_color: Color = (150, 150, 150),
        background: Color = (255, 255, 255),
        border_color: Color = (160, 160, 160),
        focus_border_color: Color = (60, 130, 240),
        border_width: int = 2,
        border_radius: int = 6,
        padding: int = 8,
        max_length: Optional[int] = None,
        allowed_chars: Optional[str] = None,
        clear_on_submit: bool = False,
        on_submit: Optional[Callable[[str], None]] = None,
        on_change: Optional[Callable[[str], None]] = None,
        anchor: str = "topleft",
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        if max_length is not None and max_length < 0:
            raise ValueError(f"max_length can't be negative (got {max_length})")
        super().__init__(pos, size, anchor=anchor, visible=visible, enabled=enabled)
        self.font = resolve_font(font, font_size)
        self.placeholder = placeholder
        self.text_color = text_color
        self.placeholder_color = placeholder_color
        self.background = background
        self.border_color = border_color
        self.focus_border_color = focus_border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.padding = padding
        self.max_length = max_length
        self.allowed_chars = allowed_chars
        self.clear_on_submit = clear_on_submit
        self.on_submit = on_submit
        self.on_change = on_change

        self._text = self._filter(text)
        self.cursor = len(self._text)
        self._focused = False
        self._blink = 0.0
        self._scroll = 0

    # ------------------------------------------------------------- properties
    @property
    def text(self) -> str:
        """The text in the box.

        Setting it moves the cursor to the end. It still respects
        ``max_length`` and ``allowed_chars``, and it does **not** call
        ``on_change``, the same as setting values on other widgets.
        """
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = self._filter(str(value))
        self.cursor = len(self._text)

    @property
    def focused(self) -> bool:
        """True while the box is receiving typing."""
        return self._focused

    @focused.setter
    def focused(self, value: bool) -> None:
        self._focused = bool(value) and self.active
        self._blink = 0.0

    # ---------------------------------------------------------------- helpers
    def _filter(self, text: str) -> str:
        if self.allowed_chars is not None:
            text = "".join(c for c in text if c in self.allowed_chars)
        if self.max_length is not None:
            text = text[: self.max_length]
        return text

    def _set_text(self, value: str) -> None:
        if value != self._text:
            self._text = value
            if self.on_change is not None:
                self.on_change(value)

    def _insert(self, chars: str) -> None:
        chars = "".join(c for c in chars if c.isprintable())
        if self.allowed_chars is not None:
            chars = "".join(c for c in chars if c in self.allowed_chars)
        if self.max_length is not None:
            chars = chars[: max(0, self.max_length - len(self._text))]
        if chars:
            self._set_text(self._text[: self.cursor] + chars + self._text[self.cursor:])
            self.cursor += len(chars)

    # ------------------------------------------------------------------ input
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle clicks (to focus) and typing. Call for every event.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if the box used the event (a click on it, or a key while
            focused). If it returns True for a key, you probably don't want your
            game to also treat that key as a movement key.
        """
        if not self.active:
            self._focused = False
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            inside = self.rect.collidepoint(event.pos)
            self.focused = inside
            if inside:
                self.cursor = self._index_at_x(event.pos[0])
            return inside

        if not self._focused:
            return False

        if event.type == pygame.TEXTINPUT:
            self._insert(event.text)
            self._blink = 0.0
            return True

        if event.type == pygame.KEYDOWN:
            self._blink = 0.0
            key = event.key
            if key == pygame.K_BACKSPACE:
                if self.cursor > 0:
                    self._set_text(self._text[: self.cursor - 1] + self._text[self.cursor:])
                    self.cursor -= 1
            elif key == pygame.K_DELETE:
                self._set_text(self._text[: self.cursor] + self._text[self.cursor + 1:])
            elif key == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif key == pygame.K_RIGHT:
                self.cursor = min(len(self._text), self.cursor + 1)
            elif key == pygame.K_HOME:
                self.cursor = 0
            elif key == pygame.K_END:
                self.cursor = len(self._text)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                submitted = self._text
                if self.clear_on_submit:
                    self._set_text("")
                    self.cursor = 0
                if self.on_submit is not None:
                    self.on_submit(submitted)
            elif key == pygame.K_ESCAPE:
                self.focused = False
            return True

        return False

    def update(self, dt: float = 0.0) -> None:
        """Make the cursor blink. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        self._blink = (self._blink + dt) % (self.CURSOR_BLINK_SECONDS * 2)

    def _index_at_x(self, x: int) -> int:
        """Character index closest to screen x position (for click-to-place cursor)."""
        local = x - (self.rect.x + self.padding) + self._scroll
        return min(
            range(len(self._text) + 1),
            key=lambda i: abs(self.font.size(self._text[:i])[0] - local),
        )

    # ---------------------------------------------------------------- drawing
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the box, its text (or placeholder) and the cursor.

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        pygame.draw.rect(surface, self.background, self.rect, border_radius=self.border_radius)

        inner = self.rect.inflate(-self.padding * 2, -self.padding * 2)
        cursor_x = self.font.size(self._text[: self.cursor])[0]
        # scroll so the cursor is always inside the box
        if cursor_x - self._scroll > inner.width:
            self._scroll = cursor_x - inner.width
        elif cursor_x - self._scroll < 0:
            self._scroll = cursor_x
        text_w = self.font.size(self._text)[0]
        self._scroll = max(0, min(self._scroll, max(0, text_w - inner.width + 2)))

        old_clip = surface.get_clip()
        surface.set_clip(inner.clip(old_clip) if old_clip else inner)
        line_h = self.font.get_height()
        text_y = inner.centery - line_h // 2
        if self._text:
            rendered = self.font.render(self._text, True, self.text_color)
            surface.blit(rendered, (inner.x - self._scroll, text_y))
        elif self.placeholder and not self._focused:
            rendered = self.font.render(self.placeholder, True, self.placeholder_color)
            surface.blit(rendered, (inner.x, text_y))
        if self._focused and self._blink < self.CURSOR_BLINK_SECONDS:
            x = inner.x + cursor_x - self._scroll
            pygame.draw.line(surface, self.text_color, (x, text_y), (x, text_y + line_h - 2), 2)
        surface.set_clip(old_clip)

        if self.border_width > 0:
            color = self.focus_border_color if self._focused else self.border_color
            pygame.draw.rect(surface, color, self.rect, self.border_width,
                             border_radius=self.border_radius)
