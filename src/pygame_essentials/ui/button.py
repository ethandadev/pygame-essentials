"""Clickable buttons, made from colored rectangles or your own images.

Quick example::

    import pygame
    import pygame_essentials as pk

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    play = pk.Button((400, 300), size=(200, 60), text="Play",
                     anchor="center", border_radius=12,
                     on_click=lambda: print("Let's go!"))

    running = True
    while running:
        dt = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            play.handle_event(event)

        screen.fill("white")
        play.draw(screen)
        pygame.display.flip()
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import pygame

from ._base import Color, FontLike, Widget, resolve_font


class Button(Widget):
    """A clickable button with hover and pressed looks.

    A click counts when the left mouse button is **pressed and released**
    over the button, just like buttons in real apps. Holding the mouse down
    counts as one click, not one per frame. Dragging off the button before
    letting go cancels the click.

    There are two ways to find out about clicks. Use whichever you like:

    * **Callback:** pass ``on_click=my_function``. It runs right away when
      the click happens.
    * **Polling:** check ``if button.was_clicked():`` in your loop. It
      returns True **once** per click, then resets.

    A button can be a **colored rectangle** (give ``size``) or an
    **image** (give ``image``; its size is used automatically).

    Args:
        pos: Position in pixels. This is the **top-left corner** unless you
            change ``anchor``.
        size: ``(width, height)`` in pixels. Needed for colored buttons. For
            image buttons you can skip it and the image's size is used. If you
            give both, the images are scaled to ``size``.
        text: Text shown in the middle of the button. Can be empty. Numbers and
            other values are converted with ``str()``.
        font: Font for the text: ``None`` (default font), a system font name
            like ``"arial"``, a ``.ttf`` path, or a ``pygame.font.Font``.
        font_size: Text size in pixels. Ignored if ``font`` is a Font object.
        text_color: Color of the text.
        color: Normal background color.
        hover_color: Background color while the mouse is over the button.
        pressed_color: Background color while the button is held down.
        disabled_color: Background color when ``enabled`` is False.
        image: A ``pygame.Surface`` to draw instead of a colored rectangle.
        hover_image: Image to show while hovering. If not given, ``image`` is
            used.
        pressed_image: Image to show while pressed. If not given,
            ``hover_image`` (or ``image``) is used.
        border_radius: How rounded the corners are, in pixels. 0 = square.
        border_width: Outline thickness in pixels. 0 = no outline.
        border_color: Outline color.
        anchor: Which point of the button ``pos`` refers to, like
            ``"center"``. See :class:`~pygame_essentials.ui.Widget`.
        on_click: A function with no arguments to call when clicked.
        visible: If False, the button is hidden and can't be clicked.
        enabled: If False, the button is grayed out and can't be clicked.

    Attributes:
        text (str): The button's text. You can change it at any time.
        hovered (bool): True while the mouse is over the button.
        pressed (bool): True while the button is being held down.
        on_click: The click callback. You can replace it later.

    Raises:
        TypeError: If you give neither ``size`` nor ``image``, or give
            ``hover_image``/``pressed_image`` without ``image``.

    Example:
        An image button, centered, checked by polling::

            start_img = pygame.image.load("start.png").convert_alpha()
            start_hover = pygame.image.load("start_hover.png").convert_alpha()
            start = pk.Button((400, 300), image=start_img,
                              hover_image=start_hover, anchor="center")

            # in your loop:
            for event in pygame.event.get():
                start.handle_event(event)
            if start.was_clicked():
                begin_game()
            start.draw(screen)
    """

    def __init__(
        self,
        pos: Sequence[float],
        size: Optional[Sequence[float]] = None,
        text: str = "",
        *,
        font: FontLike = None,
        font_size: int = 28,
        text_color: Color = (255, 255, 255),
        color: Color = (40, 40, 40),
        hover_color: Color = (62, 62, 62),
        pressed_color: Color = (25, 25, 25),
        disabled_color: Color = (130, 130, 130),
        image: Optional[pygame.Surface] = None,
        hover_image: Optional[pygame.Surface] = None,
        pressed_image: Optional[pygame.Surface] = None,
        border_radius: int = 0,
        border_width: int = 0,
        border_color: Color = (0, 0, 0),
        anchor: str = "topleft",
        on_click: Optional[Callable[[], None]] = None,
        visible: bool = True,
        enabled: bool = True,
    ) -> None:
        if size is None and image is None:
            raise TypeError(
                "Button needs either size=(width, height) for a colored button "
                "or image=<Surface> for an image button"
            )
        if image is None and (hover_image is not None or pressed_image is not None):
            raise TypeError(
                "hover_image/pressed_image were given without image. "
                "Pass image=<Surface> too"
            )
        if size is None:
            size = image.get_size()
        super().__init__(pos, size, anchor=anchor, visible=visible, enabled=enabled)

        self.text = text
        self.font = resolve_font(font, font_size)
        self.text_color = text_color
        self.color = color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.disabled_color = disabled_color
        self.border_radius = border_radius
        self.border_width = border_width
        self.border_color = border_color
        self.on_click = on_click

        self.image = self._fit(image)
        self.hover_image = self._fit(hover_image) if hover_image is not None else self.image
        self.pressed_image = (
            self._fit(pressed_image) if pressed_image is not None else self.hover_image
        )

        self._click_waiting = False
        self._text_cache: tuple = (None, None)

    def _fit(self, image: Optional[pygame.Surface]) -> Optional[pygame.Surface]:
        if image is None or image.get_size() == self.rect.size:
            return image
        try:
            return pygame.transform.smoothscale(image, self.rect.size)
        except ValueError:  # smoothscale only supports 24/32-bit images
            return pygame.transform.scale(image, self.rect.size)

    # ------------------------------------------------------------------ input
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Check whether this event hovers, presses or clicks the button.

        Call this for **every** event in your event loop.

        Args:
            event: An event from ``pygame.event.get()``.

        Returns:
            True if this event finished a click on the button.
        """
        if self._track_click(event):
            self._click_waiting = True
            if self.on_click is not None:
                self.on_click()
            return True
        return False

    def was_clicked(self) -> bool:
        """Return True **once** for each click, then reset to False.

        Use this if you'd rather check for clicks in your loop than use an
        ``on_click`` callback.

        Example::

            if quit_button.was_clicked():
                running = False
        """
        clicked = self._click_waiting
        self._click_waiting = False
        return clicked

    # ---------------------------------------------------------------- drawing
    def _current_image(self) -> Optional[pygame.Surface]:
        if self.image is None:
            return None
        if not self.enabled:
            return self.image
        if self.pressed and self.hovered:
            return self.pressed_image
        if self.hovered:
            return self.hover_image
        return self.image

    def _current_color(self) -> Color:
        if not self.enabled:
            return self.disabled_color
        if self.pressed and self.hovered:
            return self.pressed_color
        if self.hovered:
            return self.hover_color
        return self.color

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the button (background or image, outline, then text).

        Args:
            surface: Where to draw, usually your screen.
        """
        if not self.visible:
            return
        image = self._current_image()
        if image is not None:
            surface.blit(image, self.rect)
        else:
            pygame.draw.rect(surface, self._current_color(), self.rect,
                             border_radius=self.border_radius)
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, self.rect,
                             self.border_width, border_radius=self.border_radius)
        text = str(self.text)
        if text:
            key = (text, self.font, tuple(pygame.Color(self.text_color)))
            if self._text_cache[0] != key:
                rendered = self.font.render(text, True, self.text_color)
                self._text_cache = (key, rendered)
            rendered = self._text_cache[1]
            surface.blit(rendered, rendered.get_rect(center=self.rect.center))
