"""pygame-ce / classic pygame compatibility checks."""

import sys
import warnings

import pygame
import pytest

import pygame_essentials as pk
from pygame_essentials import _compat


def fake_versions(monkeypatch, **versions):
    monkeypatch.setattr(_compat, "installed_version", lambda dist: versions.get(dist.replace("-", "_")))


def test_warns_when_both_pygames_are_installed(monkeypatch):
    fake_versions(monkeypatch, pygame_ce="2.5.8", pygame="2.6.1")
    with pytest.warns(RuntimeWarning, match="Both pygame-ce 2.5.8 and pygame 2.6.1") as record:
        _compat.check_pygame()
    assert "pip uninstall -y pygame pygame-ce" in str(record[0].message)


@pytest.mark.parametrize("versions", [{"pygame_ce": "2.5.8"}, {"pygame": "2.6.1"}])
def test_no_warning_with_just_one_pygame(monkeypatch, versions):
    fake_versions(monkeypatch, **versions)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _compat.check_pygame() is pygame


def test_helpful_error_when_pygame_is_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "pygame", None)  # makes "import pygame" fail
    with pytest.raises(ImportError, match="pip install pygame-ce"):
        _compat.check_pygame()


def test_real_environment_has_only_one_pygame():
    """The environment running the tests must not have the clash we warn about."""
    assert not (_compat.installed_version("pygame-ce") and _compat.installed_version("pygame"))


def test_pygame_description_names_the_running_pygame():
    text = _compat.pygame_description()
    expected = "pygame-ce" if getattr(pygame, "IS_CE", False) else "pygame"
    assert text == f"{expected} {pygame.version.ver}"


def test_debug_overlay_shows_pygame_version():
    assert _compat.pygame_description() in pk.DebugOverlay().lines()[0]


def test_decimal_positions_are_rounded():
    button = pk.Button((10.7, 20.2), size=(50.6, 20.4))
    assert button.rect == pygame.Rect(11, 20, 51, 20)
    label = pk.Label(pygame.Vector2(99.6, 0.4), "x", anchor="center")
    assert label.rect.center == (100, 0)


@pytest.mark.skipif(not hasattr(pygame, "FRect"), reason="FRect only exists in pygame-ce")
def test_pygame_ce_frect_support():
    fr = pygame.FRect(10.6, 20.4, 30, 40)
    cam = pk.Camera((300, 300))
    assert cam.apply(fr) == pygame.Rect(11, 20, 30, 40)
    assert cam.is_visible(fr)

    class Sprite(pygame.sprite.Sprite):
        rect = pygame.FRect(500.5, 500.5, 10, 10)

    cam.follow(Sprite())
    cam.update(0.016)
    assert cam.position == pygame.Vector2(505.5 - 150, 505.5 - 150)

    debug = pk.DebugOverlay(visible=True)
    debug.draw_rect(fr)
    debug.draw(pygame.Surface((300, 300)), camera=cam)
