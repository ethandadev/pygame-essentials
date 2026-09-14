"""Simple, flexible particle effects: sparks, smoke, dust, blood, magic, confetti, rain...

Quick example::

    # a one-time explosion of sparks
    sparks = pk.ParticleEmitter(colors=[(255, 220, 90), (255, 140, 40)],
                                speed=(80, 260), lifetime=(0.3, 0.7), gravity=(0, 400))
    sparks.burst(40, pos=enemy.rect.center)

    # a steady trail of smoke behind a rocket
    smoke = pk.ParticleEmitter(rate=60, colors=[(120, 120, 120)], speed=(10, 40),
                               size=(4, 9), end_size=16, fade=True)

    # every frame:
    smoke.pos = rocket.rect.midbottom
    sparks.update(dt)
    smoke.update(dt)
    smoke.draw(screen)
    sparks.draw(screen)
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Sequence, Tuple, Union

import pygame

Range = Union[float, Tuple[float, float]]
"""Either one number (always that value) or ``(min, max)`` (a random value between them)."""


def _pick(r: Range) -> float:
    if isinstance(r, (int, float)):
        return float(r)
    return random.uniform(r[0], r[1])


class Particle:
    """One particle. You usually don't create these yourself; the emitter does.

    Attributes:
        pos (pygame.Vector2): World position.
        vel (pygame.Vector2): Velocity in pixels per second.
        age (float): Seconds since it was created.
        lifetime (float): Seconds it lives in total.
        start_size (float): Radius (or half-width) in pixels at birth.
        color (pygame.Color): Its color.
    """

    __slots__ = ("pos", "vel", "age", "lifetime", "start_size", "color")

    def __init__(self, pos, vel, lifetime, size, color) -> None:
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.age = 0.0
        self.lifetime = lifetime
        self.start_size = size
        self.color = pygame.Color(color)

    @property
    def life_fraction(self) -> float:
        """0.0 when just born, 1.0 when about to disappear."""
        return min(1.0, self.age / self.lifetime) if self.lifetime > 0 else 1.0


class ParticleEmitter:
    """Creates, moves and draws lots of small particles.

    Two ways to make particles (you can use both):

    * **Continuous:** set ``rate`` (particles per second). They appear at
      ``pos`` as long as ``emitting`` is True. Good for fire, smoke, and trails.
    * **Bursts:** call :meth:`burst` to create many at once. Good for
      explosions, hits, and pickups.

    Settings that say *Range* take either one number or a ``(min, max)``
    pair, and each particle gets a random value in that range. This
    randomness is what makes effects look natural.

    Args:
        pos: Where new particles appear (world position).
        rate: Particles created per second while ``emitting``. 0 = only
            bursts.
        lifetime: *Range*. How many seconds each particle lives.
        speed: *Range*. Starting speed in pixels per second.
        angle: The main direction particles fly, in **degrees**. 0 = right,
            90 = down, 180 = left, -90 (or 270) = up. (Pygame's y axis
            points down.)
        spread: How wide the spray is, in degrees, centered on ``angle``.
            360 = every direction (explosion). 30 = a narrow jet.
        size: *Range*. Starting radius in pixels.
        end_size: Size at the end of its life. Particles grow or shrink
            smoothly toward this. ``None`` = keep the same size.
        colors: A list of colors, and each particle picks one at random. Give
            one color for a single-colored effect.
        end_color: If given, particles fade from their color toward this
            color over their life (like fire going yellow → red).
        gravity: ``(x, y)`` acceleration in pixels per second². ``(0, 500)``
            makes particles fall and ``(0, -60)`` makes smoke rise.
        drag: How quickly particles slow down on their own. 0 = never, and 2-5
            gives a nice "puff" that stops.
        fade: If True, particles become transparent as they age.
        shape: ``"circle"`` or ``"square"``.
        max_particles: Safety limit. New particles are skipped when this
            many are alive, so your game doesn't lag.
        emitting: Whether continuous emission (``rate``) starts on.

    Attributes:
        particles (list[Particle]): All living particles.
        pos (pygame.Vector2): Spawn position. Move it to follow things.
        emitting (bool): Turn continuous emission on/off, for example only
            while a jetpack key is held.

    Every other argument is also an attribute with the same name, and you can
    change it at any time (for example ``emitter.rate = 0`` or
    ``emitter.angle += 5``).

    Example:
        Dust when the player lands::

            dust = pk.ParticleEmitter(colors=[(200, 190, 170)], angle=-90, spread=160,
                                      speed=(30, 90), size=(2, 4), end_size=0,
                                      lifetime=(0.2, 0.5), gravity=(0, 200), drag=3)
            ...
            if just_landed:
                dust.burst(12, pos=player.rect.midbottom)
    """

    def __init__(
        self,
        pos: Sequence[float] = (0, 0),
        *,
        rate: float = 0,
        lifetime: Range = (0.5, 1.0),
        speed: Range = (50, 150),
        angle: float = -90,
        spread: float = 360,
        size: Range = (2, 5),
        end_size: Optional[float] = 0,
        colors: Sequence = ((255, 255, 255),),
        end_color=None,
        gravity: Sequence[float] = (0, 0),
        drag: float = 0.0,
        fade: bool = False,
        shape: str = "circle",
        max_particles: int = 2000,
        emitting: bool = True,
    ) -> None:
        self.pos = pygame.Vector2(pos)
        self.rate = rate
        self.lifetime = lifetime
        self.speed = speed
        self.angle = angle
        self.spread = spread
        self.size = size
        self.end_size = end_size
        self.colors = colors
        self.end_color = end_color
        self.gravity = gravity
        self.drag = drag
        self.fade = fade
        self.shape = shape
        self.max_particles = max_particles
        self.emitting = emitting
        self.particles: List[Particle] = []
        self._spawn_debt = 0.0

    # These are properties so that plain tuples like ``emitter.pos = (10, 20)``
    # or ``emitter.gravity = (0, 300)`` are converted and keep working.
    @property
    def pos(self) -> pygame.Vector2:
        """Where new particles appear. You can set it to a tuple or a Vector2."""
        return self._pos

    @pos.setter
    def pos(self, value: Sequence[float]) -> None:
        self._pos = pygame.Vector2(value)

    @property
    def gravity(self) -> pygame.Vector2:
        """Acceleration in pixels per second². You can set it to a tuple or a Vector2."""
        return self._gravity

    @gravity.setter
    def gravity(self, value: Sequence[float]) -> None:
        self._gravity = pygame.Vector2(value)

    @property
    def colors(self) -> List[pygame.Color]:
        """The colors new particles pick from. You can set it to any list of colors."""
        return self._colors

    @colors.setter
    def colors(self, value: Sequence) -> None:
        if not value:
            raise ValueError("colors needs at least one color")
        self._colors = [pygame.Color(c) for c in value]

    @property
    def end_color(self) -> Optional[pygame.Color]:
        """The color particles fade toward, or ``None``."""
        return self._end_color

    @end_color.setter
    def end_color(self, value) -> None:
        self._end_color = pygame.Color(value) if value is not None else None

    @property
    def shape(self) -> str:
        """``"circle"`` or ``"square"``."""
        return self._shape

    @shape.setter
    def shape(self, value: str) -> None:
        if value not in ("circle", "square"):
            raise ValueError(f'shape must be "circle" or "square" (got {value!r})')
        self._shape = value

    def _spawn(self, pos) -> None:
        if len(self.particles) >= self.max_particles:
            return
        direction = self.angle + random.uniform(-self.spread / 2, self.spread / 2)
        vel = pygame.Vector2(_pick(self.speed), 0).rotate(direction)
        self.particles.append(
            Particle(pos, vel, max(0.01, _pick(self.lifetime)), max(0.0, _pick(self.size)),
                     random.choice(self.colors))
        )

    def burst(self, count: int, pos: Optional[Sequence[float]] = None) -> None:
        """Create ``count`` particles at once.

        Args:
            count: How many particles.
            pos: Where to create them. Defaults to the emitter's ``pos``.
        """
        spawn_at = self.pos if pos is None else pygame.Vector2(pos)
        for _ in range(int(count)):
            self._spawn(spawn_at)

    def update(self, dt: float) -> None:
        """Create new particles (if ``rate`` > 0), move all of them, and remove dead ones.

        Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        if self.emitting and self.rate > 0:
            self._spawn_debt += self.rate * dt
            whole = int(self._spawn_debt)
            self._spawn_debt -= whole
            for _ in range(whole):
                self._spawn(self.pos)

        slow = math.exp(-self.drag * dt) if self.drag else 1.0
        alive = []
        for p in self.particles:
            p.age += dt
            if p.age >= p.lifetime:
                continue
            p.vel += self.gravity * dt
            if slow != 1.0:
                p.vel *= slow
            p.pos += p.vel * dt
            alive.append(p)
        self.particles = alive

    def clear(self) -> None:
        """Remove every particle immediately."""
        self.particles.clear()

    def __len__(self) -> int:
        return len(self.particles)

    @property
    def alive_count(self) -> int:
        """How many particles are alive right now."""
        return len(self.particles)

    def draw(self, surface: pygame.Surface, camera=None) -> None:
        """Draw every particle.

        Args:
            surface: Where to draw, usually your screen.
            camera: Optional :class:`~pygame_toolkit.Camera`. If given, particles
                are treated as being in world coordinates and moved by the
                camera.
        """
        for p in self.particles:
            t = p.life_fraction
            size = p.start_size if self.end_size is None else p.start_size + (self.end_size - p.start_size) * t
            if size < 0.5:
                continue
            color = p.color if self.end_color is None else p.color.lerp(self.end_color, t)
            x, y = camera.apply(p.pos) if camera is not None else (round(p.pos.x), round(p.pos.y))
            r = max(1, round(size))
            if self.fade:
                alpha = round(color.a * (1 - t))
                if alpha <= 0:
                    continue
                dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                c = (color.r, color.g, color.b, alpha)
                if self.shape == "circle":
                    pygame.draw.circle(dot, c, (r, r), r)
                else:
                    dot.fill(c)
                surface.blit(dot, (x - r, y - r))
            elif self.shape == "circle":
                pygame.draw.circle(surface, color, (x, y), r)
            else:
                surface.fill(color, (x - r, y - r, r * 2, r * 2))
