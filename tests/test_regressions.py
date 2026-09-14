"""Tests for bugs found during the full review pass."""

from pathlib import Path

import pygame
import pytest

from conftest import click, down, motion, up
from pygame_kit import (
    Button, Camera, Checkbox, Dropdown, ParticleEmitter, Slider, TextInput, Toggle, resolve_font,
)


def test_toggle_shows_new_state_without_update():
    t = Toggle((0, 0), size=(60, 30), knob_color=(255, 0, 0), on_color=(0, 255, 0), off_color=(0, 0, 255))
    t.checked = True  # never calling update()
    screen = pygame.Surface((80, 40))
    t.draw(screen)
    right_side = screen.get_at((t.box_rect.right - 10, t.box_rect.centery))[:3]
    assert right_side == (255, 0, 0)  # the knob is on the right


def test_toggle_still_animates_with_update():
    t = Toggle((0, 0), slide_time=1.0)
    t.update(0)
    t.checked = True
    t.update(0.5)
    assert t._knob == pytest.approx(0.5)


def test_camera_accepts_tuples_for_vectors():
    cam = Camera((100, 100))
    cam.position = (50, 60)
    cam.offset = (0, -10)
    cam.world_rect = (0, 0, 1000, 1000)
    assert isinstance(cam.position, pygame.Vector2)
    assert cam.view_rect.topleft == (50, 60)
    cam.follow((500, 500))
    cam.follow_speed = 5
    cam.update(0.1)
    assert isinstance(cam.position, pygame.Vector2)


def test_particle_emitter_accepts_tuples_after_creation():
    em = ParticleEmitter(lifetime=1)
    em.pos = (10, 20)
    em.gravity = (0, 300)
    em.colors = [(255, 0, 0), "blue"]
    em.end_color = (0, 0, 0)
    em.pos.x += 5
    em.burst(5)
    em.update(0.1)
    em.draw(pygame.Surface((50, 50)))
    assert em.particles[0].vel.y == pytest.approx(30, abs=200)
    with pytest.raises(ValueError):
        em.colors = []
    with pytest.raises(ValueError):
        em.shape = "hexagon"


def test_text_input_setter_is_silent_but_typing_is_not():
    changes = []
    box = TextInput((0, 0), on_change=changes.append, max_length=4)
    box.text = "hello"
    assert box.text == "hell" and changes == []
    box.focused = True
    box.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, mod=0, unicode="", scancode=0))
    assert changes == ["hel"]


def test_text_input_clear_on_submit_reports_change():
    changes = []
    box = TextInput((0, 0), text="hi", clear_on_submit=True, on_change=changes.append)
    box.focused = True
    box.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", scancode=0))
    assert box.text == "" and box.cursor == 0 and changes == [""]


def test_font_cache_survives_font_quit():
    font = resolve_font(None, 17)
    pygame.font.quit()
    fresh = resolve_font(None, 17)
    assert fresh is not font
    fresh.render("still works", True, (0, 0, 0))


def test_resolve_font_accepts_path(tmp_path):
    ttf = Path(pygame.font.get_default_font())
    if not ttf.is_absolute():
        ttf = Path(pygame.__file__).parent / ttf
    assert resolve_font(ttf, 20).size("x")[0] > 0


def test_button_non_string_text():
    screen = pygame.Surface((100, 50))
    Button((0, 0), size=(100, 50), text=42).draw(screen)


def test_checkbox_label_change_resizes():
    cb = Checkbox((0, 0), label="Hi")
    short = cb.rect.width
    cb.label = "A much longer label"
    assert cb.rect.width > short
    assert click(cb, (cb.rect.right - 2, cb.rect.centery))


def test_dropdown_right_click_on_open_list_is_consumed():
    d = Dropdown((0, 0), ["a", "b", "c"], size=(100, 30))
    d.open()
    assert d.handle_event(down((10, 45), button=3)) is True
    assert d.is_open and d.selected == "a"


def test_slider_zero_width_does_not_crash():
    s = Slider((0, 0), size=(0, 8))
    s.handle_event(down((0, 4)))
