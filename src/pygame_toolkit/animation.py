"""Cut spritesheets into frames and play them as animations.

* :class:`Spritesheet`: one image with many frames in a grid, split into
  separate Surfaces.
* :class:`Animation`: plays a list of frames at a set speed.
* :class:`AnimationSet`: a group of named animations (``"idle"``,
  ``"run"``, ``"jump"``) where only one plays at a time.

Quick example::

    sheet = pk.Spritesheet("player.png", 32, 32, scale=3)
    player_anims = pk.AnimationSet({
        "idle": pk.Animation(sheet.frames(row=0), fps=6),
        "run":  pk.Animation(sheet.frames(row=1), fps=12),
        "jump": pk.Animation(sheet.frames(row=2, count=4), fps=10, loop=False),
    })

    # every frame:
    player_anims.play("run" if moving else "idle")   # safe to call every frame
    player_anims.update(dt)
    image = player_anims.image
    if facing_left:
        image = pygame.transform.flip(image, True, False)
    screen.blit(image, player_rect)
"""

from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional, Sequence, Union

import pygame


class Spritesheet:
    """Splits a grid-shaped image into individual frames.

    Frames are counted from the **top-left**: column 0 row 0 is the first
    frame, and columns go left to right, rows top to bottom.

    Args:
        image: A ``pygame.Surface``, or a file path like ``"assets/player.png"``.
            Paths are loaded for you, and ``convert_alpha()`` is applied if a
            display window exists.
        frame_width: Width of **one** frame in the original image, in pixels.
        frame_height: Height of **one** frame in the original image, in
            pixels.
        margin: Empty pixels around the outside edge of the whole sheet.
        spacing: Empty pixels between neighboring frames.
        scale: Enlarge every frame by this factor. ``scale=3`` turns 16x16
            pixel art into 48x48. Uses plain (crisp) scaling, which is right for
            pixel art.

    Attributes:
        image (pygame.Surface): The whole sheet.
        columns (int): How many frames fit across.
        rows (int): How many frames fit down.

    Raises:
        ValueError: If a frame size isn't positive, or the frame is bigger
            than the sheet.
        FileNotFoundError: If ``image`` is a path that doesn't exist.

    Example::

        sheet = pk.Spritesheet("coins.png", 16, 16, scale=2)
        spin = pk.Animation(sheet.frames(), fps=12)   # every frame on the sheet
    """

    def __init__(
        self,
        image: Union[pygame.Surface, str, os.PathLike],
        frame_width: int,
        frame_height: int,
        *,
        margin: int = 0,
        spacing: int = 0,
        scale: float = 1,
    ) -> None:
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("frame_width and frame_height must be positive")
        if not isinstance(image, pygame.Surface):
            path = os.fspath(image)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Spritesheet image not found: {path!r}")
            image = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
        self.image = image
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.margin = margin
        self.spacing = spacing
        self.scale = scale
        w, h = image.get_size()
        self.columns = (w - 2 * margin + spacing) // (frame_width + spacing)
        self.rows = (h - 2 * margin + spacing) // (frame_height + spacing)
        if self.columns < 1 or self.rows < 1:
            raise ValueError(
                f"a {frame_width}x{frame_height} frame doesn't fit in a {w}x{h} sheet"
            )
        self._cache: Dict[tuple, pygame.Surface] = {}

    def frame(self, column: int, row: int = 0) -> pygame.Surface:
        """Get one frame by its grid position.

        Args:
            column: Which column, starting at 0 on the left.
            row: Which row, starting at 0 at the top.

        Returns:
            A new Surface for that frame (scaled if ``scale`` was set). The
            same frame is only cut out once and then reused.

        Raises:
            IndexError: If the column or row is outside the sheet.
        """
        if not (0 <= column < self.columns and 0 <= row < self.rows):
            raise IndexError(
                f"frame ({column}, {row}) is outside the sheet "
                f"({self.columns} columns x {self.rows} rows)"
            )
        key = (column, row)
        surf = self._cache.get(key)
        if surf is None:
            x = self.margin + column * (self.frame_width + self.spacing)
            y = self.margin + row * (self.frame_height + self.spacing)
            surf = self.image.subsurface((x, y, self.frame_width, self.frame_height)).copy()
            if self.scale != 1:
                size = (round(self.frame_width * self.scale), round(self.frame_height * self.scale))
                surf = pygame.transform.scale(surf, size)
            self._cache[key] = surf
        return surf

    def frames(self, row: Optional[int] = None, start: int = 0, count: Optional[int] = None) -> List[pygame.Surface]:
        """Get several frames in order, ready to pass to :class:`Animation`.

        Args:
            row: Only take frames from this row. If ``None``, take every frame
                on the sheet, reading left-to-right, top-to-bottom like a book.
            start: Skip this many frames first.
            count: How many frames to take. ``None`` = all remaining frames.
                Useful when the last row isn't full.

        Returns:
            A list of Surfaces.

        Example::

            walk = sheet.frames(row=2, count=6)   # first 6 frames of row 2
        """
        if row is None:
            cells = [(c, r) for r in range(self.rows) for c in range(self.columns)]
        else:
            cells = [(c, row) for c in range(self.columns)]
        cells = cells[start:] if count is None else cells[start:start + count]
        return [self.frame(c, r) for c, r in cells]


class Animation:
    """Plays a list of frames at a chosen speed.

    Call ``update(dt)`` every frame and draw ``animation.image``.

    Args:
        frames: The images to play, in order. Usually from
            :meth:`Spritesheet.frames`, but any list of Surfaces works, for example
            ``[pygame.image.load(f"walk{i}.png") for i in range(4)]``.
        fps: Animation frames per second. This is **not** your game's FPS: 10
            means each image shows for 0.1 seconds.
        loop: If True, start over at the end. If False, stop on the last
            frame and set ``finished``.
        on_finish: Function with no arguments called when a non-looping
            animation reaches its end. Good for "remove the explosion when
            it's done".
        playing: If False, it starts paused on the first frame.

    Attributes:
        frames (list): The frames.
        fps (float): Speed. You can change it while playing, for example to
            run faster as the player speeds up.
        loop (bool): Whether it loops.
        frame_index (int): Which frame is showing.
        playing (bool): False while paused or finished.
        finished (bool): True once a non-looping animation has ended.

    Raises:
        ValueError: If ``frames`` is empty or ``fps`` isn't positive.

    Example::

        explosion = pk.Animation(sheet.frames(row=4), fps=20, loop=False,
                                 on_finish=lambda: effects.remove(explosion))
    """

    def __init__(
        self,
        frames: Sequence[pygame.Surface],
        fps: float = 10,
        *,
        loop: bool = True,
        on_finish: Optional[Callable[[], None]] = None,
        playing: bool = True,
    ) -> None:
        if not frames:
            raise ValueError("an Animation needs at least one frame")
        if fps <= 0:
            raise ValueError(f"fps must be positive (got {fps})")
        self.frames = list(frames)
        self.fps = fps
        self.loop = loop
        self.on_finish = on_finish
        self.playing = playing
        self.finished = False
        self.frame_index = 0
        self._time = 0.0

    @property
    def image(self) -> pygame.Surface:
        """The frame to draw right now."""
        return self.frames[self.frame_index]

    @property
    def duration(self) -> float:
        """How long one full play-through takes, in seconds."""
        return len(self.frames) / self.fps

    def update(self, dt: float) -> None:
        """Move the animation forward in time. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        if not self.playing:
            return
        self._time += dt
        frame_time = 1.0 / self.fps
        while self._time >= frame_time:
            self._time -= frame_time
            if self.frame_index + 1 < len(self.frames):
                self.frame_index += 1
            elif self.loop:
                self.frame_index = 0
            else:
                self._time = 0.0
                self.playing = False
                self.finished = True
                if self.on_finish is not None:
                    self.on_finish()
                break

    def play(self) -> None:
        """Continue playing. If a non-looping animation had finished, it starts over."""
        if self.finished:
            self.restart()
        self.playing = True

    def pause(self) -> None:
        """Freeze on the current frame."""
        self.playing = False

    def restart(self) -> None:
        """Jump back to the first frame and play."""
        self.frame_index = 0
        self._time = 0.0
        self.finished = False
        self.playing = True

    def flipped(self, horizontal: bool = True, vertical: bool = False) -> "Animation":
        """Make a mirrored copy, for example a left-facing walk from a right-facing one.

        Args:
            horizontal: Mirror left↔right.
            vertical: Mirror upside-down.

        Returns:
            A new, independent Animation with the same speed and settings.

        Example::

            walk_right = pk.Animation(sheet.frames(row=1), fps=10)
            walk_left = walk_right.flipped()
        """
        return Animation(
            [pygame.transform.flip(f, horizontal, vertical) for f in self.frames],
            self.fps, loop=self.loop, on_finish=self.on_finish, playing=self.playing,
        )


class AnimationSet:
    """A group of named animations where only one plays at a time, like idle/run/jump for a player.

    The key feature is :meth:`play`: calling ``play("run")`` every frame
    is safe, because it only restarts the animation when you **switch** to a
    different one. No more animations stuck on frame 0.

    Args:
        animations: A dict of name → :class:`Animation`.
        start: Name of the animation to start with. Defaults to the first
            one in the dict.

    Attributes:
        animations (dict): The animations by name. You can add more later.
        current_name (str): Name of the animation playing now.

    Raises:
        ValueError: If ``animations`` is empty.
        KeyError: If ``start`` (or a name passed to ``play``) doesn't exist.

    Example::

        anims = pk.AnimationSet({"idle": idle, "run": run})
        ...
        anims.play("run" if abs(velocity.x) > 0 else "idle")
        anims.update(dt)
        screen.blit(anims.image, rect)
    """

    def __init__(self, animations: Dict[str, Animation], start: Optional[str] = None) -> None:
        if not animations:
            raise ValueError("AnimationSet needs at least one animation")
        self.animations = dict(animations)
        self.current_name = start if start is not None else next(iter(self.animations))
        if self.current_name not in self.animations:
            raise KeyError(f"no animation named {self.current_name!r}")

    @property
    def current(self) -> Animation:
        """The :class:`Animation` object playing now."""
        return self.animations[self.current_name]

    @property
    def image(self) -> pygame.Surface:
        """The frame to draw right now."""
        return self.current.image

    def play(self, name: str, restart: bool = False) -> None:
        """Switch to the animation called ``name``.

        If it's already the current animation, nothing happens (unless
        ``restart=True``), so you can call this every frame.

        Args:
            name: Which animation to play.
            restart: Start it from frame 0 even if it's already playing.

        Raises:
            KeyError: If there's no animation with that name. The error
                lists the names that exist.
        """
        if name not in self.animations:
            raise KeyError(f"no animation named {name!r} (have: {', '.join(self.animations)})")
        if name != self.current_name or restart:
            self.current_name = name
            self.current.restart()

    def update(self, dt: float) -> None:
        """Advance the current animation. Call once per frame.

        Args:
            dt: Seconds since the last frame.
        """
        self.current.update(dt)
