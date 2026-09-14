"""An F3-style debug overlay: FPS, mouse position, your own values, and hitbox outlines.

Quick example::

    debug = pk.DebugOverlay()                       # press F3 to show/hide
    debug.watch("player pos", lambda: player.rect.topleft)
    debug.watch("enemies", lambda: len(enemies))

    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            debug.handle_event(event)
        debug.update(dt)
        ...
        for enemy in enemies:
            debug.draw_rect(enemy.rect)             # only shows while the overlay is on
        debug.draw(screen)                          # draw last so it's on top
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, List, Optional, Sequence, Tuple

import pygame

from .ui._base import Color, FontLike, resolve_font


class DebugOverlay:
    """A toggleable info panel for finding bugs while you play.

    It shows:

    * **FPS** (averaged, so it doesn't flicker) and frame time in milliseconds
    * **Mouse position** (also in world coordinates if you pass a camera to
      ``draw``)
    * **Watched values**: anything you add with :meth:`watch`
    * **Hitboxes**: outlines of Rects you pass to :meth:`draw_rect`

    When the overlay is hidden, ``watch`` functions aren't called and
    ``draw_rect`` does nothing, so you can leave the debug calls in your
    game and they cost almost nothing.

    Args:
        toggle_key: Key that shows/hides the overlay. ``None`` = no key; set
            ``visible`` yourself.
        visible: Whether it starts shown.
        position: Top-left of the panel on screen, in pixels.
        font: Font for the text. Monospace fonts like ``"menlo"`` or
            ``"consolas"`` line up nicely.
        font_size: Text size in pixels.
        text_color: Text color.
        background: Panel color. A 4th number is transparency (0-255).
        hitbox_color: Default outline color for :meth:`draw_rect`.

    Attributes:
        visible (bool): Whether the overlay is showing. You can set it.
        fps (float): Smoothed frames per second, updated by :meth:`update`.

    Example::

        debug = pk.DebugOverlay(visible=True, font="menlo")
        debug.watch("velocity", lambda: f"{player.vel.x:.1f}, {player.vel.y:.1f}")
        debug.watch("on ground", lambda: player.on_ground)
    """

    def __init__(
        self,
        *,
        toggle_key: Optional[int] = pygame.K_F3,
        visible: bool = False,
        position: Sequence[int] = (8, 8),
        font: FontLike = None,
        font_size: int = 20,
        text_color: Color = (255, 255, 255),
        background: Color = (0, 0, 0, 170),
        hitbox_color: Color = (255, 0, 255),
    ) -> None:
        self.toggle_key = toggle_key
        self.visible = visible
        self.position = (int(position[0]), int(position[1]))
        self.font = resolve_font(font, font_size)
        self.text_color = text_color
        self.background = pygame.Color(background)
        self.hitbox_color = hitbox_color
        self.fps = 0.0
        self._frame_ms = 0.0
        self._watches: "OrderedDict[str, Callable[[], Any]]" = OrderedDict()
        self._rects: List[Tuple[pygame.Rect, Color, int]] = []

    # ---------------------------------------------------------------- controls
    def toggle(self) -> None:
        """Show the overlay if it's hidden, or hide it if it's showing."""
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Watch for the toggle key. Call for every event.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if the event was the toggle key press.
        """
        if self.toggle_key is not None and event.type == pygame.KEYDOWN and event.key == self.toggle_key:
            self.toggle()
            return True
        return False

    def watch(self, name: str, getter: Callable[[], Any]) -> None:
        """Show a live value in the overlay.

        Args:
            name: Label shown before the value, like ``"speed"``.
            getter: A function with no arguments that returns the value, like
                ``lambda: player.speed``. It's called every frame while the
                overlay is visible. Use a **function**, not the value itself,
                or it would never change.

        Example::

            debug.watch("state", lambda: player.state)
        """
        self._watches[name] = getter

    def unwatch(self, name: str) -> None:
        """Stop showing a watched value. Doesn't complain if it wasn't watched."""
        self._watches.pop(name, None)

    def draw_rect(self, rect: pygame.Rect, color: Optional[Color] = None, width: int = 1) -> None:
        """Outline a Rect (like a hitbox) the next time :meth:`draw` runs.

        Call it every frame for each thing you want to see, **before**
        ``draw``. It does nothing while the overlay is hidden.

        Args:
            rect: The Rect to outline. It uses world coordinates if you give
                ``draw`` a camera.
            color: Outline color. Defaults to ``hitbox_color``.
            width: Line thickness in pixels.
        """
        if self.visible:
            self._rects.append((pygame.Rect(rect), color or self.hitbox_color, width))

    # ------------------------------------------------------------ per-frame
    def update(self, dt: float) -> None:
        """Measure FPS. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        if dt <= 0:
            return
        blend = 0.1  # smooth the numbers so they're readable
        self._frame_ms += (dt * 1000 - self._frame_ms) * (1.0 if self._frame_ms == 0 else blend)
        self.fps = 1000 / self._frame_ms if self._frame_ms > 0 else 0.0

    def lines(self, camera=None) -> List[str]:
        """The text lines the overlay shows. Handy if you want to print them instead.

        Args:
            camera: Optional :class:`~pygame_essentials.Camera` to also show the
                mouse's world position.
        """
        mx, my = pygame.mouse.get_pos()
        out = [f"FPS: {self.fps:.0f}  ({self._frame_ms:.1f} ms)", f"Mouse: {mx}, {my}"]
        if camera is not None:
            wx, wy = camera.to_world((mx, my))
            out.append(f"World: {wx:.0f}, {wy:.0f}")
        for name, getter in self._watches.items():
            try:
                value = getter()
            except Exception as exc:  # a broken watch shouldn't crash the game
                value = f"<error: {type(exc).__name__}: {exc}>"
            out.append(f"{name}: {value}")
        return out

    def draw(self, surface: pygame.Surface, camera=None) -> None:
        """Draw hitboxes and the info panel. Call this **last** so it's on top of everything.

        Args:
            surface: Where to draw, usually your screen.
            camera: Optional :class:`~pygame_essentials.Camera`. If given, hitboxes are
                moved by the camera and the mouse's world position is shown.
        """
        rects, self._rects = self._rects, []
        if not self.visible:
            return
        for rect, color, width in rects:
            pygame.draw.rect(surface, color, camera.apply(rect) if camera is not None else rect, width)

        rendered = [self.font.render(line, True, self.text_color) for line in self.lines(camera)]
        pad, gap = 6, 2
        w = max(r.get_width() for r in rendered) + pad * 2
        h = sum(r.get_height() for r in rendered) + gap * (len(rendered) - 1) + pad * 2
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill(self.background)
        y = pad
        for r in rendered:
            panel.blit(r, (pad, y))
            y += r.get_height() + gap
        surface.blit(panel, self.position)
