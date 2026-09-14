"""Timers and cooldowns, so you don't have to track time with extra variables.

* :class:`Timer`: "do something after X seconds" (once, or repeating).
* :class:`Cooldown`: "don't let this happen more than once every X seconds".

Both work on ``dt`` (seconds since the last frame), so they behave the same
at 30 FPS, 60 FPS or 144 FPS, and they pause automatically when you stop
calling ``update``, for example while your game is paused.

Quick example::

    clock = pygame.time.Clock()
    spawn_timer = pk.Timer(2.0, spawn_enemy, repeat=True)   # every 2 seconds
    dash = pk.Cooldown(1.5)

    while running:
        dt = clock.tick(60) / 1000
        spawn_timer.update(dt)
        dash.update(dt)

        if keys[pygame.K_LSHIFT] and dash.use():
            player.dash()
"""

from __future__ import annotations

from typing import Callable, Optional


class Timer:
    """Counts down and calls a function when time is up. It can repeat.

    Remember to call ``update(dt)`` every frame, or the timer never
    finishes.

    Args:
        duration: How long to wait, in **seconds**.
        on_done: Function with no arguments called each time the timer
            finishes. Optional: you can check ``update()``'s return value or
            ``done`` instead.
        repeat: If True, the timer starts over each time it finishes, like an
            alarm that goes off every ``duration`` seconds.
        autostart: If False, the timer waits until you call :meth:`start`.

    Attributes:
        duration (float): Seconds per countdown. You can change it; it takes
            effect immediately.
        elapsed (float): Seconds counted so far in this countdown.
        running (bool): True while counting.
        done (bool): True once a non-repeating timer has finished.
        on_done: The callback. You can replace it.

    Raises:
        ValueError: If ``duration`` is negative, or 0 with ``repeat=True``
            (that would fire forever in one frame).

    Examples:
        A one-shot timer:

        >>> fired = []
        >>> t = Timer(1.0, lambda: fired.append("boom"))
        >>> t.update(0.6)
        False
        >>> t.update(0.6)
        True
        >>> fired, t.done
        (['boom'], True)

        A repeating timer handles big frame jumps correctly:

        >>> ticks = []
        >>> t = Timer(0.5, lambda: ticks.append(1), repeat=True)
        >>> t.update(1.6)   # a laggy frame covers 3 whole repeats
        True
        >>> len(ticks), round(t.elapsed, 2)
        (3, 0.1)
    """

    def __init__(
        self,
        duration: float,
        on_done: Optional[Callable[[], None]] = None,
        *,
        repeat: bool = False,
        autostart: bool = True,
    ) -> None:
        if duration < 0:
            raise ValueError(f"duration can't be negative (got {duration})")
        if repeat and duration == 0:
            raise ValueError("a repeating Timer needs a duration greater than 0")
        self.duration = duration
        self.on_done = on_done
        self.repeat = repeat
        self.elapsed = 0.0
        self.running = autostart
        self.done = False

    # ------------------------------------------------------------ controls
    def start(self) -> None:
        """Start (or restart) the countdown from zero."""
        self.elapsed = 0.0
        self.done = False
        self.running = True

    restart = start

    def pause(self) -> None:
        """Stop counting but remember how far along it was. :meth:`resume` continues."""
        self.running = False

    def resume(self) -> None:
        """Continue counting after :meth:`pause`. Does nothing if the timer is done."""
        if not self.done:
            self.running = True

    def stop(self) -> None:
        """Stop and reset to zero without calling ``on_done``."""
        self.running = False
        self.elapsed = 0.0

    # ------------------------------------------------------------- queries
    @property
    def remaining(self) -> float:
        """Seconds left until the timer finishes (0 when done)."""
        return max(0.0, self.duration - self.elapsed)

    @property
    def progress(self) -> float:
        """How far along the countdown is, from 0.0 (just started) to 1.0 (finished).

        Great for animations or feeding a :class:`~pygame_essentials.ProgressBar`.
        """
        if self.duration == 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)

    # -------------------------------------------------------------- update
    def update(self, dt: float) -> bool:
        """Count time. Call once per frame.

        Args:
            dt: Seconds since the last frame, like ``clock.tick(60) / 1000``.

        Returns:
            True if the timer finished during this update (at least once).
        """
        if not self.running:
            return False
        self.elapsed += dt
        if self.elapsed < self.duration:
            return False
        if not self.repeat:
            self.elapsed = self.duration
            self.running = False
            self.done = True
            if self.on_done is not None:
                self.on_done()
            return True
        while self.running and self.elapsed >= self.duration:
            self.elapsed -= self.duration
            if self.on_done is not None:
                self.on_done()  # the callback may stop() the timer
        return True

    def __repr__(self) -> str:
        state = "done" if self.done else ("running" if self.running else "paused")
        return f"<Timer {self.elapsed:.2f}/{self.duration:.2f}s {state}{' repeat' if self.repeat else ''}>"


class Cooldown:
    """Limits how often something can happen, like shooting, dashing, or using a potion.

    The simplest way to use it is :meth:`use`, which checks **and** starts
    the cooldown in one step::

        if clicked and cooldown.use():
            shoot()

    Or do it in two steps with :meth:`ready` and :meth:`trigger`, if you
    need to check something in between.

    Remember to call ``update(dt)`` every frame, or the cooldown never
    finishes.

    Args:
        duration: Seconds to wait after each use before it's ready again.
        start_ready: If True (default), it can be used right away. If False,
            it starts cooling down, which is handy for "the boss can't attack in
            the first 3 seconds".

    Attributes:
        duration (float): Cooldown length in seconds. You can change it, for
            example with a fire-rate upgrade.

    Raises:
        ValueError: If ``duration`` is negative.

    Examples:
        >>> shoot = Cooldown(0.25)
        >>> shoot.use()        # first shot is allowed
        True
        >>> shoot.use()        # too soon!
        False
        >>> shoot.update(0.3)  # time passes...
        >>> shoot.use()
        True

        In a game loop::

            shoot = pk.Cooldown(0.25)
            ...
            shoot.update(dt)
            if keys[pygame.K_SPACE] and shoot.ready():
                fire_bullet()
                shoot.trigger()
    """

    def __init__(self, duration: float, *, start_ready: bool = True) -> None:
        if duration < 0:
            raise ValueError(f"duration can't be negative (got {duration})")
        self.duration = duration
        self._remaining = 0.0 if start_ready else duration

    def update(self, dt: float) -> None:
        """Count the cooldown down. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        if self._remaining > 0:
            self._remaining = max(0.0, self._remaining - dt)

    def ready(self) -> bool:
        """True if the cooldown has finished and the action can be used."""
        return self._remaining <= 0

    def trigger(self) -> None:
        """Start the cooldown now, even if it wasn't ready yet."""
        self._remaining = self.duration

    def use(self) -> bool:
        """If ready, start the cooldown and return True. Otherwise return False.

        This is the same as ``if cd.ready(): cd.trigger()`` in one call.
        """
        if self.ready():
            self.trigger()
            return True
        return False

    def reset(self) -> None:
        """Make it ready immediately, for example after picking up a power-up."""
        self._remaining = 0.0

    @property
    def remaining(self) -> float:
        """Seconds until it's ready again (0 if ready)."""
        return self._remaining

    @property
    def progress(self) -> float:
        """How recharged it is, from 0.0 (just used) to 1.0 (ready).

        Perfect for drawing an ability icon filling up.
        """
        if self.duration == 0:
            return 1.0
        return 1.0 - self._remaining / self.duration

    def __repr__(self) -> str:
        return f"<Cooldown {'ready' if self.ready() else f'{self._remaining:.2f}s left'}>"
