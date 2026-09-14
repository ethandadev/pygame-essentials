import json

import pygame
import pytest

from pygame_toolkit import Camera, DebugOverlay, SaveData, default_save_folder


# ----------------------------------------------------------------- SaveData
def test_save_survives_reload(tmp_path):
    s = SaveData("Test", folder=tmp_path, defaults={"coins": 0})
    assert s["coins"] == 0
    assert not (tmp_path / "save.json").exists()  # defaults alone aren't written
    s["coins"] = 12
    s.set("colors", (255, 0, 0))
    again = SaveData("Test", folder=tmp_path, defaults={"coins": 0})
    assert again["coins"] == 12
    assert again.get("colors") == [255, 0, 0]  # tuples come back as lists
    assert json.loads((tmp_path / "save.json").read_text())["coins"] == 12


def test_save_records_and_delete(tmp_path):
    s = SaveData("Test", folder=tmp_path, defaults={"best": None})
    assert s.set_max("highscore", 10)
    assert not s.set_max("highscore", 5)
    assert s.set_max("highscore", 11) and s["highscore"] == 11
    assert s.set_min("lap", 30.5) and not s.set_min("lap", 31) and s.set_min("lap", 29)
    del s["highscore"]
    assert "highscore" not in s
    with pytest.raises(KeyError):
        s["highscore"]
    s.clear()
    assert s.data == {"best": None}


def test_save_get_returns_copy(tmp_path):
    s = SaveData("Test", folder=tmp_path)
    s["items"] = ["sword"]
    s.get("items").append("shield")
    assert s["items"] == ["sword"]


def test_save_rejects_unsaveable(tmp_path):
    s = SaveData("Test", folder=tmp_path)
    with pytest.raises(TypeError, match="can't save 'rect'"):
        s["rect"] = pygame.Rect(0, 0, 1, 1)
    with pytest.raises(TypeError):
        s.set(5, "x")


def test_save_no_autosave(tmp_path):
    s = SaveData("Test", folder=tmp_path, autosave=False)
    s["a"] = 1
    assert not (tmp_path / "save.json").exists()
    s.save()
    assert SaveData("Test", folder=tmp_path)["a"] == 1


def test_save_corrupt_file_recovers(tmp_path):
    (tmp_path / "save.json").write_text("{not json")
    with pytest.warns(RuntimeWarning):
        s = SaveData("Test", folder=tmp_path, defaults={"x": 1})
    assert s["x"] == 1
    assert (tmp_path / "save.json.corrupt").exists()


def test_default_folder_uses_game_name():
    assert default_save_folder("CoolGame").name == "CoolGame"


# ------------------------------------------------------------- DebugOverlay
def keydown(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def test_debug_toggle_and_watch():
    d = DebugOverlay()
    assert not d.visible
    assert d.handle_event(keydown(pygame.K_F3))
    assert d.visible
    hp = {"v": 5}
    d.watch("hp", lambda: hp["v"])
    d.watch("broken", lambda: 1 / 0)
    hp["v"] = 3
    lines = d.lines()
    assert "hp: 3" in lines
    assert any(line.startswith("broken: <error: ZeroDivisionError") for line in lines)
    d.unwatch("hp")
    assert "hp: 3" not in d.lines()


def test_debug_fps_smoothing():
    d = DebugOverlay()
    d.update(1 / 60)
    assert d.fps == pytest.approx(60)
    for _ in range(200):
        d.update(1 / 30)
    assert d.fps == pytest.approx(30, rel=0.01)


def test_debug_draws_hitboxes_only_when_visible():
    screen = pygame.Surface((300, 300))
    d = DebugOverlay(hitbox_color=(255, 0, 255), position=(0, 0))
    d.draw_rect(pygame.Rect(200, 200, 50, 50))
    d.draw(screen)
    assert screen.get_at((200, 220))[:3] == (0, 0, 0)
    d.visible = True
    cam = Camera((300, 300))
    cam.position.update(100, 100)
    d.draw_rect(pygame.Rect(200, 200, 50, 50))
    d.draw(screen, camera=cam)
    assert screen.get_at((100, 120))[:3] == (255, 0, 255)  # moved by the camera
