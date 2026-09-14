import pygame
import pytest

from conftest import click, down, motion, up
from pygame_toolkit import Button, Label


def test_click_fires_once_on_release():
    calls = []
    b = Button((100, 100), size=(100, 50), on_click=lambda: calls.append(1))
    b.handle_event(motion((120, 120)))
    assert b.hovered
    b.handle_event(down((120, 120)))
    assert b.pressed and calls == []  # holding down is not a click yet
    for _ in range(10):
        b.handle_event(motion((121, 121)))
    assert b.handle_event(up((121, 121))) is True
    assert calls == [1]
    assert b.was_clicked() is True
    assert b.was_clicked() is False  # resets after reading


def test_dragging_off_cancels_click():
    b = Button((100, 100), size=(100, 50))
    b.handle_event(down((120, 120)))
    b.handle_event(motion((500, 500)))
    assert b.handle_event(up((500, 500))) is False
    assert not b.was_clicked()


def test_press_outside_release_inside_is_not_click():
    b = Button((100, 100), size=(100, 50))
    b.handle_event(down((0, 0)))
    assert b.handle_event(up((120, 120))) is False


def test_right_click_ignored():
    b = Button((0, 0), size=(50, 50))
    b.handle_event(down((10, 10), button=3))
    assert b.handle_event(up((10, 10), button=3)) is False


def test_image_button_hover_uses_image_size_and_anchor():
    img = pygame.Surface((80, 40))
    b = Button((400, 300), image=img, anchor="center")
    assert b.rect.size == (80, 40)
    assert b.rect.center == (400, 300)
    b.handle_event(motion((365, 285)))  # inside the centered image
    assert b.hovered
    b.handle_event(motion((395, 330)))  # below it
    assert not b.hovered


def test_images_scaled_to_size():
    b = Button((0, 0), size=(30, 30), image=pygame.Surface((10, 10)))
    assert b.image.get_size() == (30, 30)


def test_disabled_button_ignores_clicks():
    b = Button((0, 0), size=(50, 50), enabled=False)
    assert click(b, (10, 10)) is False


def test_invalid_args_raise():
    with pytest.raises(TypeError):
        Button((0, 0))
    with pytest.raises(TypeError):
        Button((0, 0), size=(10, 10), hover_image=pygame.Surface((5, 5)))
    with pytest.raises(ValueError):
        Button((0, 0), size=(10, 10), anchor="middle")


def test_button_draws_colors():
    screen = pygame.Surface((200, 200))
    b = Button((10, 10), size=(50, 50), color=(255, 0, 0), hover_color=(0, 255, 0))
    b.draw(screen)
    assert screen.get_at((30, 30))[:3] == (255, 0, 0)
    b.handle_event(motion((30, 30)))
    b.draw(screen)
    assert screen.get_at((30, 30))[:3] == (0, 255, 0)


def test_label_resizes_and_keeps_anchor():
    lbl = Label((700, 20), "1", anchor="topright")
    w1 = lbl.rect.width
    lbl.text = 123456
    assert lbl.text == "123456"
    assert lbl.rect.width > w1
    assert lbl.rect.topright == (700, 20)


def test_label_padding():
    lbl = Label((0, 0), "hi", padding=10)
    plain = Label((0, 0), "hi")
    assert lbl.rect.width == plain.rect.width + 20
