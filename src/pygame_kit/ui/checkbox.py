"""On/off controls: a classic :class:`Checkbox` and a phone-style :class:`Toggle` switch.

Quick example::

    music = pk.Toggle((20, 20), checked=True, label="Music",
                      on_change=lambda on: pygame.mixer.music.set_volume(1 if on else 0))
    fullscreen = pk.Checkbox((20, 60), label="Fullscreen")

    # in your loop:
    for event in pygame.event.get():
        music.handle_event(event)
        fullscreen.handle_event(event)
    music.update(dt)          # animates the switch sliding
    music.draw(screen)
    fullscreen.draw(screen)
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence, Tuple

import pygame

from ._base import Color, FontLike, Widget, resolve_font


class Checkbox(Widget):
    """A square box that is checked or unchecked when clicked, with an optional text label.

    Clicking the **label text** toggles it too, so it's easy to hit.

    Args:
        pos: Position in pixels. This is the **top-left corner** unless you
            change ``anchor``.
        size: Width/height of the square box in pixels.
        checked: Whether it starts checked.
        label: Text shown to the right of the box. Can be empty.
        font: Font for the label: ``None``, a system font name, a ``.ttf``
            path, or a ``pygame.font.Font``.
        font_size: Label text size in pixels.
        label_color: Label text color.
        box_color: Background of the box.
        check_color: Color of the check mark, and the box fill when checked.
        border_color: Outline color of the box.
        label_gap: Space in pixels between the box and the label.
        on_change: Function called as ``on_change(checked)`` with True/False
            whenever it's clicked.
        anchor: Which point of the whole widget (box + label) ``pos`` refers to.
        visible: If False, it's hidden and ignores clicks.
        enabled: If False, it's grayed out and ignores clicks.

    Attributes:
        checked (bool): Whether it is checked. You can set it from code (this
            does **not** call ``on_change``).

    Example::

        show_fps = pk.Checkbox((20, 20), label="Show FPS")
        ...
        if show_fps.checked:
            draw_fps()
    """

    def __init__(
        self,
        pos: Sequence[float],
        size: int = 24,
        *,
        checked: bool = False,
        label: str = "",
        font: FontLike = None,
        font_size: int = 28,
        label_color: Color = (30, 30, 30),
        box_color: Color = (255, 255, 255),
        check_color: Color = (60, 130, 240),
        border_color: Color = (140, 140, 140),
        label_gap: int = 8,
        on_change: Optional[Callable[[bool], None]] = None,
        anchor: str = "topleft",
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        self.font = resolve_font(font, font_size)
        self.label = label
        self.label_color = label_color
        self.label_gap = label_gap
        self.box_size = self._control_size(size)
        total = self._total_size()
        super().__init__(pos, total, anchor=anchor, visible=visible, enabled=enabled)
        self.checked = checked
        self.box_color = box_color
        self.check_color = check_color
        self.border_color = border_color
        self.on_change = on_change

    def _control_size(self, size) -> Tuple[int, int]:
        return (int(size), int(size))

    def _total_size(self) -> Tuple[int, int]:
        w, h = self.box_size
        if self.label:
            lw, lh = self.font.size(self.label)
            return (w + self.label_gap + lw, max(h, lh))
        return (w, h)

    @property
    def box_rect(self) -> pygame.Rect:
        """Where the box/switch itself is drawn (without the label)."""
        r = pygame.Rect((0, 0), self.box_size)
        r.midleft = self.rect.midleft
        return r

    def toggle(self) -> None:
        """Flip between checked and unchecked, and call ``on_change``."""
        self.checked = not self.checked
        if self.on_change is not None:
            self.on_change(self.checked)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Toggle when clicked. Call for every event.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if this event toggled it.
        """
        if self._track_click(event):
            self.toggle()
            return True
        return False

    def _draw_label(self, surface: pygame.Surface) -> None:
        if self.label:
            color = self.label_color if self.enabled else (150, 150, 150)
            text = self.font.render(self.label, True, color)
            box = self.box_rect
            surface.blit(text, text.get_rect(midleft=(box.right + self.label_gap, box.centery)))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the box, the check mark (if checked) and the label.

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        box = self.box_rect
        radius = max(2, box.width // 6)
        accent = self.check_color if self.enabled else (170, 170, 170)
        if self.checked:
            pygame.draw.rect(surface, accent, box, border_radius=radius)
            w, h = box.size
            points = [
                (box.x + w * 0.22, box.y + h * 0.52),
                (box.x + w * 0.42, box.y + h * 0.72),
                (box.x + w * 0.78, box.y + h * 0.30),
            ]
            pygame.draw.lines(surface, (255, 255, 255), False, points, max(2, w // 8))
        else:
            pygame.draw.rect(surface, self.box_color, box, border_radius=radius)
            border = self.check_color if self.hovered and self.enabled else self.border_color
            pygame.draw.rect(surface, border, box, 2, border_radius=radius)
        self._draw_label(surface)


class Toggle(Checkbox):
    """A sliding on/off switch, like the ones in phone settings.

    It works exactly like :class:`Checkbox` (same ``checked``, ``on_change``,
    and ``label``), but looks like a switch. The knob slides smoothly if you
    call ``update(dt)`` each frame. If you don't, it just jumps.

    Args:
        pos: Position in pixels. This is the **top-left corner** unless you
            change ``anchor``.
        size: ``(width, height)`` of the switch in pixels.
        checked: Whether it starts switched on.
        label: Text shown to the right of the switch.
        on_color: Track color when on.
        off_color: Track color when off.
        knob_color: Color of the round knob.
        slide_time: How long the knob takes to slide across, in seconds.
        **kwargs: Everything else :class:`Checkbox` accepts (``font``,
            ``font_size``, ``label_color``, ``on_change``, ``anchor``, ...).

    Example::

        sfx = pk.Toggle((20, 20), label="Sound effects", checked=True)
        ...
        sfx.update(dt)
        sfx.draw(screen)
        if sfx.checked:
            jump_sound.play()
    """

    def __init__(
        self,
        pos: Sequence[float],
        size: Sequence[int] = (50, 28),
        *,
        checked: bool = False,
        label: str = "",
        on_color: Color = (60, 190, 100),
        off_color: Color = (190, 190, 190),
        knob_color: Color = (255, 255, 255),
        slide_time: float = 0.12,
        **kwargs,
    ) -> None:
        super().__init__(pos, size, checked=checked, label=label, **kwargs)
        self.on_color = on_color
        self.off_color = off_color
        self.knob_color = knob_color
        self.slide_time = slide_time
        self._knob = 1.0 if checked else 0.0

    def _control_size(self, size) -> Tuple[int, int]:
        return (int(size[0]), int(size[1]))

    def update(self, dt: float = 0.0) -> None:
        """Slide the knob toward its on/off position. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        target = 1.0 if self.checked else 0.0
        if self.slide_time <= 0:
            self._knob = target
            return
        step = dt / self.slide_time
        if self._knob < target:
            self._knob = min(target, self._knob + step)
        else:
            self._knob = max(target, self._knob - step)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the switch track, the knob and the label.

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        box = self.box_rect
        t = self._knob
        off, on = pygame.Color(self.off_color), pygame.Color(self.on_color)
        track = off.lerp(on, t) if self.enabled else pygame.Color(210, 210, 210)
        pygame.draw.rect(surface, track, box, border_radius=box.height // 2)
        r = box.height // 2 - 3
        x = box.x + 3 + r + t * (box.width - 6 - 2 * r)
        pygame.draw.circle(surface, self.knob_color, (round(x), box.centery), r)
        self._draw_label(surface)
