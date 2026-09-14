"""A 2D camera that follows the player, shakes, and converts between world and screen positions.

The idea: your game world can be much bigger than the window. Everything
keeps its **world position** (where it really is in the level), and the
camera decides which part of the world is visible. When you draw, you ask
the camera where that thing lands **on screen**.

Quick example::

    camera = pk.Camera(screen.get_size(), world_rect=level_rect, follow_speed=6)

    while running:
        dt = clock.tick(60) / 1000
        ...
        camera.follow(player.rect)
        camera.update(dt)

        if player_got_hit:
            camera.shake(8, 0.3)

        screen.fill("skyblue")
        for block in blocks:
            if camera.is_visible(block.rect):          # skip off-screen things
                screen.blit(block.image, camera.apply(block.rect))
        screen.blit(player.image, camera.apply(player.rect))

        # clicking in the world? convert the mouse position:
        world_mouse = camera.to_world(pygame.mouse.get_pos())
"""

from __future__ import annotations

import math
import random
from typing import Any, Optional, Sequence, Tuple, Union

import pygame

Point = Union[Tuple[float, float], Sequence[float], pygame.Vector2]

# pygame-ce also has FRect (a Rect with float positions); regular pygame doesn't.
_RECT_TYPES = (pygame.Rect, pygame.FRect) if hasattr(pygame, "FRect") else (pygame.Rect,)


class Camera:
    """Follows a target smoothly, stays inside the level, and can shake.

    Args:
        screen_size: ``(width, height)`` of the window, like
            ``screen.get_size()``.
        world_rect: The level's size and position as a ``pygame.Rect``. The
            camera never shows anything outside it. ``None`` = no limits.
        follow_speed: How quickly the camera catches up to its target.
            ``None`` = snap instantly (no smoothing). Around ``4``-``10``
            feels smooth. Bigger numbers are snappier.
        offset: Shift where the target sits on screen, in pixels. ``(0, 0)``
            keeps the target centered. ``(0, -80)`` shows more of what's
            **above** the player (the camera looks 80px higher).
        deadzone: ``(width, height)`` of a box in the middle of the screen
            where the target can move **without** the camera moving. This is
            common in platformers so small movements don't jiggle the view.
            ``None`` = no deadzone.

    Attributes:
        position (pygame.Vector2): World position of the **top-left** of the
            view. Set it directly to jump the camera (see also
            :meth:`snap_to`).
        screen_size (tuple): The window size you passed in.
        world_rect (pygame.Rect | None): The level limits. You can change them.
        follow_speed (float | None): Smoothing. You can change it.
        offset (pygame.Vector2): See ``offset`` above.

    Example:
        Zelda-style camera that snaps, for a 2000x1500 level::

            cam = pk.Camera((800, 600), world_rect=pygame.Rect(0, 0, 2000, 1500))
    """

    def __init__(
        self,
        screen_size: Sequence[int],
        *,
        world_rect: Optional[pygame.Rect] = None,
        follow_speed: Optional[float] = None,
        offset: Point = (0, 0),
        deadzone: Optional[Sequence[int]] = None,
    ) -> None:
        self.screen_size = (int(screen_size[0]), int(screen_size[1]))
        self.world_rect = pygame.Rect(world_rect) if world_rect is not None else None
        self.follow_speed = follow_speed
        self.offset = pygame.Vector2(offset)
        self.deadzone = tuple(deadzone) if deadzone is not None else None
        self.position = pygame.Vector2(0, 0)
        self._target: Any = None
        self._shake_strength = 0.0
        self._shake_time = 0.0
        self._shake_duration = 0.0
        self._shake_offset = pygame.Vector2(0, 0)

    # ------------------------------------------------------------- following
    @staticmethod
    def _point_of(target: Any) -> pygame.Vector2:
        if hasattr(target, "rect"):
            target = target.rect
        if isinstance(target, _RECT_TYPES):
            return pygame.Vector2(target.center)
        return pygame.Vector2(target)

    def follow(self, target: Any) -> None:
        """Set what the camera follows. It moves toward it in :meth:`update`.

        Args:
            target: A ``pygame.Rect`` (the camera centers on it), a position like
                ``(x, y)`` or ``Vector2``, any object with a ``.rect``
                (like a pygame Sprite), or ``None`` to stop following.

        Tip:
            Passing a Rect or sprite **object** means the camera keeps
            tracking it as it moves, so you only need to call ``follow``
            once. A tuple like ``(x, y)`` is a fixed point.
        """
        self._target = target

    def _desired_position(self) -> pygame.Vector2:
        w, h = self.screen_size
        center = self._point_of(self._target) + self.offset
        if self.deadzone is not None:
            view_center = self.position + (w / 2, h / 2)
            dz_w, dz_h = self.deadzone[0] / 2, self.deadzone[1] / 2
            dx = center.x - view_center.x
            dy = center.y - view_center.y
            shift_x = dx - dz_w if dx > dz_w else dx + dz_w if dx < -dz_w else 0
            shift_y = dy - dz_h if dy > dz_h else dy + dz_h if dy < -dz_h else 0
            return self._clamped(self.position + (shift_x, shift_y))
        return self._clamped(center - (w / 2, h / 2))

    def _clamped(self, pos: pygame.Vector2) -> pygame.Vector2:
        if self.world_rect is None:
            return pygame.Vector2(pos)
        w, h = self.screen_size
        wr = self.world_rect
        x = wr.centerx - w / 2 if wr.width <= w else max(wr.left, min(pos.x, wr.right - w))
        y = wr.centery - h / 2 if wr.height <= h else max(wr.top, min(pos.y, wr.bottom - h))
        return pygame.Vector2(x, y)

    def snap_to(self, target: Any = None) -> None:
        """Jump straight to the target with no smoothing, for example when a level starts or after a teleport.

        Args:
            target: What to jump to (same kinds as :meth:`follow`). If
                ``None``, uses the current follow target.
        """
        if target is not None:
            self._target = target
        if self._target is not None:
            w, h = self.screen_size
            center = self._point_of(self._target) + self.offset
            self.position = self._clamped(center - (w / 2, h / 2))

    def shake(self, strength: float = 6, duration: float = 0.25) -> None:
        """Shake the screen, which is great for hits, explosions, and landings.

        The shake fades out over ``duration`` and the camera returns exactly
        to where it should be. Shaking again while already shaking uses the
        stronger of the two.

        Args:
            strength: How far the view jumps around, in pixels. 3 is subtle
                and 15 is huge.
            duration: How long it lasts, in seconds.
        """
        if strength >= self._current_shake_strength():
            self._shake_strength = strength
            self._shake_duration = max(duration, 1e-6)
            self._shake_time = duration

    def _current_shake_strength(self) -> float:
        if self._shake_time <= 0:
            return 0.0
        return self._shake_strength * (self._shake_time / self._shake_duration)

    @property
    def is_shaking(self) -> bool:
        """True while a shake is still happening."""
        return self._shake_time > 0

    def update(self, dt: float) -> None:
        """Move toward the target and update the shake. Call once per frame, **before** drawing.

        Args:
            dt: Seconds since the last frame.
        """
        if self._target is not None:
            desired = self._desired_position()
            if self.follow_speed is None:
                self.position = desired
            else:
                # frame-rate independent smoothing
                t = 1 - math.exp(-self.follow_speed * dt)
                self.position += (desired - self.position) * t
        elif self.world_rect is not None:
            self.position = self._clamped(self.position)

        if self._shake_time > 0:
            self._shake_time = max(0.0, self._shake_time - dt)
            s = self._current_shake_strength()
            self._shake_offset = pygame.Vector2(random.uniform(-s, s), random.uniform(-s, s))
        else:
            self._shake_offset = pygame.Vector2(0, 0)

    # ------------------------------------------------------------ converting
    @property
    def _draw_offset(self) -> pygame.Vector2:
        return self.position + self._shake_offset

    def apply(self, thing: Union[pygame.Rect, Point]) -> Union[pygame.Rect, Tuple[int, int]]:
        """Convert a world Rect or position to where it should be drawn **on screen**.

        Args:
            thing: A ``pygame.Rect`` or a position ``(x, y)`` in world
                coordinates.

        Returns:
            A new Rect (same size, moved), or an ``(x, y)`` tuple of ints,
            ready for ``screen.blit`` or ``pygame.draw``.

        Example::

            screen.blit(enemy.image, camera.apply(enemy.rect))
            pygame.draw.circle(screen, "red", camera.apply(bullet_pos), 4)
        """
        off = self._draw_offset
        if isinstance(thing, _RECT_TYPES):
            return pygame.Rect(round(thing.x - off.x), round(thing.y - off.y), thing.width, thing.height)
        return (round(thing[0] - off.x), round(thing[1] - off.y))

    to_screen = apply

    def to_world(self, screen_pos: Point) -> pygame.Vector2:
        """Convert a screen position (like the mouse) to a world position.

        Args:
            screen_pos: A position on the window, like ``pygame.mouse.get_pos()``.

        Returns:
            The matching world position as a ``pygame.Vector2``.

        Example::

            if event.type == pygame.MOUSEBUTTONDOWN:
                place_block_at(camera.to_world(event.pos))
        """
        return pygame.Vector2(screen_pos) + self._draw_offset

    @property
    def view_rect(self) -> pygame.Rect:
        """The part of the world currently on screen, as a Rect in world coordinates."""
        return pygame.Rect(round(self.position.x), round(self.position.y), *self.screen_size)

    def is_visible(self, rect: pygame.Rect, margin: int = 0) -> bool:
        """True if a world Rect is at least partly on screen.

        Use this to skip drawing things that are off-screen, which helps a lot
        in big levels.

        Args:
            rect: The thing's world Rect.
            margin: Count things this many pixels outside the screen as
                visible too, so nothing pops in at the edge.
        """
        return self.view_rect.inflate(margin * 2, margin * 2).colliderect(rect)
