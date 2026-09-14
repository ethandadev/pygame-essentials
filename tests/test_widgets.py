import pygame
import pytest

from conftest import click, down, motion, up
from pygame_toolkit import Checkbox, Dropdown, ProgressBar, Slider, TextInput, Toggle


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def typed(text):
    return pygame.event.Event(pygame.TEXTINPUT, text=text)


# ---------------------------------------------------------------- TextInput
def test_text_input_needs_focus_then_types():
    box = TextInput((0, 0), size=(200, 40))
    assert box.handle_event(typed("a")) is False
    box.handle_event(down((10, 10)))
    assert box.focused
    for ch in "hello":
        box.handle_event(typed(ch))
    box.handle_event(key(pygame.K_BACKSPACE))
    assert box.text == "hell"
    box.handle_event(key(pygame.K_HOME))
    box.handle_event(typed("X"))
    assert box.text == "Xhell"
    box.handle_event(key(pygame.K_END))
    box.handle_event(key(pygame.K_LEFT))
    box.handle_event(key(pygame.K_DELETE))
    assert box.text == "Xhel"


def test_text_input_click_outside_unfocuses():
    box = TextInput((0, 0), size=(200, 40))
    box.focused = True
    box.handle_event(down((500, 500)))
    assert not box.focused


def test_text_input_submit_and_clear():
    got = []
    box = TextInput((0, 0), on_submit=got.append, clear_on_submit=True)
    box.focused = True
    box.handle_event(typed("gg"))
    box.handle_event(key(pygame.K_RETURN))
    assert got == ["gg"]
    assert box.text == ""


def test_text_input_max_length_and_allowed_chars():
    changes = []
    box = TextInput((0, 0), max_length=3, allowed_chars="0123456789", on_change=changes.append)
    box.focused = True
    box.handle_event(typed("1a2b345"))
    assert box.text == "123"
    assert changes == ["123"]
    with pytest.raises(ValueError):
        TextInput((0, 0), max_length=-1)


def test_text_input_draws_long_text_without_error():
    screen = pygame.Surface((300, 100))
    box = TextInput((0, 0), size=(100, 40), text="a very long piece of text that scrolls")
    box.focused = True
    box.update(0.1)
    box.draw(screen)


# ------------------------------------------------------------------- Slider
def test_slider_click_and_drag_with_step():
    values = []
    s = Slider((100, 100), size=(200, 8), min_value=0, max_value=10, step=1, on_change=values.append)
    s.handle_event(down((100 + 200 * 0.34, 104)))
    assert s.dragging and s.value == 3
    s.handle_event(motion((100 + 200 * 0.76, 104)))
    assert s.value == 8
    s.handle_event(motion((1000, 104)))  # far right clamps
    assert s.value == 10
    s.handle_event(up((1000, 104)))
    assert not s.dragging
    assert values == [3, 8, 10]


def test_slider_value_setter_clamps_and_snaps():
    s = Slider((0, 0), min_value=0, max_value=1, step=0.1)
    s.value = 0.33
    assert s.value == 0.3
    s.value = 5
    assert s.value == 1
    with pytest.raises(ValueError):
        Slider((0, 0), min_value=5, max_value=5)
    with pytest.raises(ValueError):
        Slider((0, 0), step=0)


# -------------------------------------------------------- Checkbox / Toggle
def test_checkbox_toggles_including_label_click():
    seen = []
    cb = Checkbox((0, 0), label="Fullscreen", on_change=seen.append)
    assert click(cb, cb.box_rect.center)
    label_point = (cb.rect.right - 3, cb.rect.centery)
    assert click(cb, label_point)
    assert seen == [True, False]


def test_toggle_knob_slides_with_update():
    t = Toggle((0, 0), slide_time=0.2)
    click(t, t.box_rect.center)
    assert t.checked
    t.update(0.1)
    assert 0.4 < t._knob < 0.6
    t.update(1.0)
    assert t._knob == 1.0
    t.draw(pygame.Surface((100, 50)))


# ----------------------------------------------------------------- Dropdown
def test_dropdown_open_select_close():
    picked = []
    d = Dropdown((0, 0), ["Low", "Medium", "High"], size=(100, 30), on_change=picked.append)
    assert d.selected == "Low"
    assert d.handle_event(down((10, 10)))
    assert d.is_open
    # third option is at y = 30 (box) + 2 * 30
    assert d.handle_event(down((10, 30 + 2 * 30 + 5)))
    assert not d.is_open
    assert d.selected == "High" and d.selected_index == 2
    assert picked == ["High"]


def test_dropdown_click_outside_closes_and_passes_through():
    d = Dropdown((0, 0), ["a", "b"], size=(100, 30))
    d.open()
    assert d.handle_event(down((500, 500))) is False
    assert not d.is_open


def test_dropdown_scrolls():
    d = Dropdown((0, 0), [str(i) for i in range(20)], size=(100, 30), max_visible=5)
    d.open()
    d.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-3, flipped=False))
    d.handle_event(down((10, 35)))  # first visible row
    assert d.selected == "3"
    d.open()
    d.draw(pygame.Surface((200, 300)))


def test_dropdown_bad_index():
    with pytest.raises(ValueError):
        Dropdown((0, 0), ["a"], selected_index=4)


# ------------------------------------------------------------- ProgressBar
def test_progress_bar_set_from_and_clamp():
    bar = ProgressBar((0, 0))
    bar.set_from(25, 50)
    assert bar.value == 0.5 and bar.shown_value == 0.5
    bar.value = 7
    assert bar.value == 1.0
    bar.set_from(3, 0)
    assert bar.value == 0.0


def test_progress_bar_smooth_and_trail():
    bar = ProgressBar((0, 0), smooth=True, speed=1.0, trail_color=(255, 255, 0))
    bar.value = 0.5
    assert bar.shown_value == 1.0
    bar.update(0.25)
    assert bar.shown_value == pytest.approx(0.75)
    assert bar._trail == 1.0  # trail waits before shrinking
    for _ in range(40):
        bar.update(0.05)
    assert bar.shown_value == 0.5 and bar._trail == 0.5


def test_progress_bar_draws_fill():
    screen = pygame.Surface((200, 40))
    bar = ProgressBar((0, 0), size=(200, 20), value=0.5, fill_color=(0, 255, 0),
                      background=(0, 0, 0), border_radius=0, show_text=True)
    bar.draw(screen)
    assert screen.get_at((10, 10))[:3] == (0, 255, 0)
    assert screen.get_at((190, 10))[:3] == (0, 0, 0)
