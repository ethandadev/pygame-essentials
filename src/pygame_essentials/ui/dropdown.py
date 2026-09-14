"""A dropdown menu for choosing one option from a list.

Quick example::

    quality = pk.Dropdown((20, 20), ["Low", "Medium", "High"], selected_index=1,
                          on_change=lambda option: print("Quality:", option))

    # in your loop. Give the dropdown events FIRST and draw it LAST:
    for event in pygame.event.get():
        if quality.handle_event(event):
            continue            # the dropdown used this click, so skip everything else
        other_button.handle_event(event)

    other_button.draw(screen)
    quality.draw(screen)        # drawn last so the open list covers other things
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence

import pygame

from ._base import Color, FontLike, Widget, resolve_font


class Dropdown(Widget):
    """A box that opens a list of options when clicked, and closes when you pick one.

    * Click the box to open or close the list.
    * Click an option to select it. ``on_change(option)`` is called.
    * Click anywhere else to close it without changing anything.
    * If there are more options than ``max_visible``, scroll with the mouse
      wheel.

    Important:
        While open, the list hangs **below** the box, over other widgets. So:

        1. Call the dropdown's ``handle_event`` **before** other widgets',
           and skip the event if it returns True. Otherwise a click on an
           option could also click a button hidden under the list.
        2. Call the dropdown's ``draw`` **after** other widgets, so the list
           appears on top.

    Args:
        pos: Position of the closed box in pixels. This is the **top-left
            corner** unless you change ``anchor``.
        options: The choices. Usually strings, but anything works: they are
            shown with ``str()``, and ``selected`` gives you back the original
            object.
        size: ``(width, height)`` of the closed box. Each option in the list
            has the same height.
        selected_index: Index of the option selected at the start, or
            ``None`` to start with nothing selected (shows ``placeholder``).
        placeholder: Text shown when nothing is selected.
        max_visible: How many options are shown at once before scrolling.
        font: ``None``, a system font name, a ``.ttf`` path, or a
            ``pygame.font.Font``.
        font_size: Text size in pixels.
        text_color: Color of the text.
        background: Background of the box and the list.
        hover_color: Background of the option under the mouse.
        selected_color: Background of the currently selected option in the
            list.
        border_color: Outline color.
        border_radius: How rounded the corners are, in pixels.
        padding: Space in pixels left of the text.
        on_change: Function called as ``on_change(option)`` when the player
            picks a different option.
        anchor: Which point of the closed box ``pos`` refers to.
        visible: If False, it's hidden and ignores input.
        enabled: If False, it can't be opened.

    Attributes:
        options (list): The list of options. If you change it, also check
            that ``selected_index`` is still valid.
        selected_index (int | None): Index of the selected option. You can set
            it from code (this does **not** call ``on_change``).
        is_open (bool): True while the list is showing.

    Raises:
        ValueError: If ``selected_index`` is outside the options list, or
            ``max_visible`` is less than 1.

    Example:
        Picking a resolution::

            sizes = [(800, 600), (1280, 720), (1920, 1080)]
            res = pk.Dropdown((20, 20), sizes, size=(180, 36), selected_index=0)
            ...
            width, height = res.selected
    """

    def __init__(
        self,
        pos: Sequence[float],
        options: Sequence[Any],
        size: Sequence[float] = (200, 36),
        *,
        selected_index: Optional[int] = 0,
        placeholder: str = "Select...",
        max_visible: int = 6,
        font: FontLike = None,
        font_size: int = 26,
        text_color: Color = (30, 30, 30),
        background: Color = (255, 255, 255),
        hover_color: Color = (225, 235, 255),
        selected_color: Color = (240, 240, 240),
        border_color: Color = (160, 160, 160),
        border_radius: int = 6,
        padding: int = 10,
        on_change: Optional[Callable[[Any], None]] = None,
        anchor: str = "topleft",
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        self.options: List[Any] = list(options)
        if not self.options:
            selected_index = None
        if selected_index is not None and not 0 <= selected_index < len(self.options):
            raise ValueError(
                f"selected_index {selected_index} is out of range for {len(self.options)} options"
            )
        if max_visible < 1:
            raise ValueError(f"max_visible must be at least 1 (got {max_visible})")
        super().__init__(pos, size, anchor=anchor, visible=visible, enabled=enabled)
        self.selected_index = selected_index
        self.placeholder = placeholder
        self.max_visible = max_visible
        self.font = resolve_font(font, font_size)
        self.text_color = text_color
        self.background = background
        self.hover_color = hover_color
        self.selected_color = selected_color
        self.border_color = border_color
        self.border_radius = border_radius
        self.padding = padding
        self.on_change = on_change
        self.is_open = False
        self._scroll = 0
        self._hover_index: Optional[int] = None

    # ------------------------------------------------------------------ state
    @property
    def selected(self) -> Any:
        """The selected option itself (not its index), or ``None`` if nothing is selected."""
        if self.selected_index is None:
            return None
        return self.options[self.selected_index]

    def open(self) -> None:
        """Open the list, scrolled so the selected option is visible."""
        if not self.active or not self.options:
            return
        self.is_open = True
        if self.selected_index is not None:
            self._scroll = min(max(0, self.selected_index - self.max_visible + 1), self._max_scroll())
        else:
            self._scroll = 0

    def close(self) -> None:
        """Close the list without changing the selection."""
        self.is_open = False
        self._hover_index = None

    def _max_scroll(self) -> int:
        return max(0, len(self.options) - self.max_visible)

    @property
    def list_rect(self) -> pygame.Rect:
        """The area the open list covers (below the box)."""
        rows = min(self.max_visible, len(self.options))
        return pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, rows * self.rect.height)

    def _index_at(self, pos) -> Optional[int]:
        lr = self.list_rect
        if not lr.collidepoint(pos):
            return None
        i = self._scroll + (pos[1] - lr.y) // self.rect.height
        return i if i < len(self.options) else None

    # ------------------------------------------------------------------ input
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Open, close, scroll and select. Call for every event, **before** other widgets.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if the dropdown used the event. When True, don't pass the
            event on to widgets underneath.
        """
        if not self.active:
            self.close()
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            if self.is_open:
                self._hover_index = self._index_at(event.pos)
                return self._hover_index is not None
            return False

        if event.type == pygame.MOUSEWHEEL and self.is_open:
            self._scroll = max(0, min(self._max_scroll(), self._scroll - event.y))
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.is_open:
                    self.close()
                else:
                    self.open()
                return True
            if self.is_open:
                index = self._index_at(event.pos)
                self.close()
                if index is not None:
                    if index != self.selected_index:
                        self.selected_index = index
                        if self.on_change is not None:
                            self.on_change(self.options[index])
                    return True
                return False  # clicked elsewhere: close, but let the click through

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and self.is_open:
            return self.list_rect.collidepoint(event.pos)  # e.g. a right-click on the list

        return False

    # ---------------------------------------------------------------- drawing
    def _draw_arrow(self, surface: pygame.Surface) -> None:
        cx, cy = self.rect.right - 16, self.rect.centery
        s = 5
        if self.is_open:
            pts = [(cx - s, cy + s // 2), (cx + s, cy + s // 2), (cx, cy - s // 2 - 1)]
        else:
            pts = [(cx - s, cy - s // 2), (cx + s, cy - s // 2), (cx, cy + s // 2 + 1)]
        pygame.draw.polygon(surface, self.text_color, pts)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the box and, if open, the list of options. Draw this **after** other widgets.

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        bg = self.hover_color if (self.hovered and self.enabled) else self.background
        pygame.draw.rect(surface, bg, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.border_color, self.rect, 1, border_radius=self.border_radius)
        label = str(self.selected) if self.selected_index is not None else self.placeholder
        color = self.text_color if self.enabled and self.selected_index is not None else (150, 150, 150)
        text = self.font.render(label, True, color)
        clip = surface.get_clip()
        surface.set_clip(pygame.Rect(self.rect.x, self.rect.y, self.rect.width - 30, self.rect.height).clip(clip))
        surface.blit(text, text.get_rect(midleft=(self.rect.x + self.padding, self.rect.centery)))
        surface.set_clip(clip)
        self._draw_arrow(surface)

        if not self.is_open:
            return
        lr = self.list_rect
        pygame.draw.rect(surface, self.background, lr, border_radius=self.border_radius)
        h = self.rect.height
        end = min(len(self.options), self._scroll + self.max_visible)
        for row, i in enumerate(range(self._scroll, end)):
            r = pygame.Rect(lr.x, lr.y + row * h, lr.width, h)
            if i == self._hover_index:
                pygame.draw.rect(surface, self.hover_color, r)
            elif i == self.selected_index:
                pygame.draw.rect(surface, self.selected_color, r)
            t = self.font.render(str(self.options[i]), True, self.text_color)
            surface.blit(t, t.get_rect(midleft=(r.x + self.padding, r.centery)))
        if self._max_scroll() > 0:  # scrollbar
            bar_h = max(12, lr.height * self.max_visible // len(self.options))
            bar_y = lr.y + (lr.height - bar_h) * self._scroll // self._max_scroll()
            pygame.draw.rect(surface, (180, 180, 180), (lr.right - 6, bar_y, 4, bar_h), border_radius=2)
        pygame.draw.rect(surface, self.border_color, lr, 1, border_radius=self.border_radius)
