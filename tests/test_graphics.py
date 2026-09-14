import random

import pygame
import pytest

from pygame_essentials import Animation, AnimationSet, Camera, ParticleEmitter, Spritesheet


def make_sheet(cols=4, rows=2, w=10, h=8, spacing=0, margin=0):
    surf = pygame.Surface((margin * 2 + cols * w + (cols - 1) * spacing,
                           margin * 2 + rows * h + (rows - 1) * spacing))
    for r in range(rows):
        for c in range(cols):
            x = margin + c * (w + spacing)
            y = margin + r * (h + spacing)
            surf.fill((c * 50, r * 100, 7), (x, y, w, h))
    return surf


# -------------------------------------------------------------- Spritesheet
def test_spritesheet_grid_and_frames():
    sheet = Spritesheet(make_sheet(), 10, 8)
    assert (sheet.columns, sheet.rows) == (4, 2)
    assert len(sheet.frames()) == 8
    row1 = sheet.frames(row=1, start=1, count=2)
    assert [f.get_at((0, 0))[:3] for f in row1] == [(50, 100, 7), (100, 100, 7)]
    with pytest.raises(IndexError):
        sheet.frame(4, 0)


def test_spritesheet_spacing_margin_scale():
    sheet = Spritesheet(make_sheet(spacing=2, margin=3), 10, 8, spacing=2, margin=3, scale=2)
    assert (sheet.columns, sheet.rows) == (4, 2)
    f = sheet.frame(3, 1)
    assert f.get_size() == (20, 16)
    assert f.get_at((19, 15))[:3] == (150, 100, 7)


def test_spritesheet_errors(tmp_path):
    with pytest.raises(ValueError):
        Spritesheet(pygame.Surface((5, 5)), 10, 10)
    with pytest.raises(FileNotFoundError):
        Spritesheet(tmp_path / "missing.png", 10, 10)


def test_spritesheet_loads_from_path(tmp_path):
    path = tmp_path / "sheet.png"
    pygame.image.save(make_sheet(), str(path))
    assert Spritesheet(path, 10, 8).columns == 4


# ---------------------------------------------------------------- Animation
def frames(n):
    return [pygame.Surface((1, 1)) for _ in range(n)]


def test_animation_loops_at_fps():
    a = Animation(frames(4), fps=10)
    a.update(0.25)
    assert a.frame_index == 2
    a.update(0.2)
    assert a.frame_index == 0  # wrapped around
    assert a.duration == pytest.approx(0.4)


def test_animation_non_loop_finishes_once():
    done = []
    a = Animation(frames(3), fps=10, loop=False, on_finish=lambda: done.append(1))
    a.update(1.0)
    assert a.finished and a.frame_index == 2 and done == [1]
    a.update(1.0)
    assert done == [1]
    a.play()
    assert a.frame_index == 0 and a.playing


def test_animation_flipped_and_errors():
    img = pygame.Surface((2, 1))
    img.set_at((0, 0), (255, 0, 0))
    flipped = Animation([img], fps=5).flipped()
    assert flipped.image.get_at((1, 0))[:3] == (255, 0, 0)
    with pytest.raises(ValueError):
        Animation([], fps=5)
    with pytest.raises(ValueError):
        Animation(frames(1), fps=0)


def test_animation_set_only_restarts_on_switch():
    idle, run = Animation(frames(4), fps=10), Animation(frames(4), fps=10)
    anims = AnimationSet({"idle": idle, "run": run})
    assert anims.current_name == "idle"
    anims.play("run")
    anims.update(0.25)
    anims.play("run")  # calling every frame must not reset
    assert run.frame_index == 2
    with pytest.raises(KeyError):
        anims.play("fly")


# ------------------------------------------------------------------- Camera
def test_camera_snap_follow_and_apply():
    cam = Camera((800, 600))
    target = pygame.Rect(1000, 1000, 20, 20)
    cam.follow(target)
    cam.update(1 / 60)
    assert cam.position == pygame.Vector2(1010 - 400, 1010 - 300)
    assert cam.apply(target).center == (400, 300)
    assert cam.to_world((400, 300)) == pygame.Vector2(1010, 1010)
    assert cam.apply((1010, 1010)) == (400, 300)


def test_camera_follows_moving_rect_object():
    cam = Camera((100, 100))
    player = pygame.Rect(0, 0, 10, 10)
    cam.follow(player)
    player.x = 500
    cam.update(0.016)
    assert cam.view_rect.centerx == 505


def test_camera_smoothing_moves_part_way():
    cam = Camera((100, 100), follow_speed=5)
    cam.follow((1000, 0))
    cam.update(0.1)
    assert 0 < cam.position.x < 950


def test_camera_world_limits():
    cam = Camera((800, 600), world_rect=pygame.Rect(0, 0, 2000, 1000))
    cam.snap_to((10, 10))
    assert cam.position == pygame.Vector2(0, 0)
    cam.snap_to((1990, 990))
    assert cam.position == pygame.Vector2(1200, 400)
    small = Camera((800, 600), world_rect=pygame.Rect(0, 0, 400, 300))
    small.snap_to((0, 0))
    assert small.view_rect.center == (200, 150)  # small levels are centered


def test_camera_deadzone():
    cam = Camera((200, 200), deadzone=(100, 100))
    cam.snap_to((100, 100))
    cam.follow((130, 100))  # inside deadzone: no movement
    cam.update(0.016)
    assert cam.position == pygame.Vector2(0, 0)
    cam.follow((180, 100))  # 30px past the deadzone edge
    cam.update(0.016)
    assert cam.position.x == pytest.approx(30)


def test_camera_shake_returns_to_zero():
    random.seed(1)
    cam = Camera((100, 100))
    cam.shake(10, 0.2)
    cam.update(0.05)
    assert cam.is_shaking
    assert cam.apply((0, 0)) != (0, 0)
    for _ in range(10):
        cam.update(0.05)
    assert not cam.is_shaking
    assert cam.apply((0, 0)) == (0, 0)


def test_camera_is_visible():
    cam = Camera((100, 100))
    assert cam.is_visible(pygame.Rect(50, 50, 5, 5))
    assert not cam.is_visible(pygame.Rect(150, 50, 5, 5))
    assert cam.is_visible(pygame.Rect(105, 50, 5, 5), margin=10)


# ---------------------------------------------------------------- Particles
def test_particles_burst_move_and_die():
    em = ParticleEmitter((100, 100), lifetime=0.5, speed=100, angle=0, spread=0, gravity=(0, 0))
    em.burst(10)
    assert len(em) == 10
    em.update(0.1)
    assert all(p.pos.x == pytest.approx(110) for p in em.particles)
    em.update(0.5)
    assert em.alive_count == 0


def test_particles_rate_is_frame_rate_independent():
    em = ParticleEmitter(rate=100, lifetime=10)
    for _ in range(60):
        em.update(1 / 60)
    assert 99 <= len(em) <= 100
    em.emitting = False
    em.update(1)
    assert 99 <= len(em) <= 100


def test_particles_max_and_gravity_and_draw():
    em = ParticleEmitter(max_particles=5, speed=0, gravity=(0, 100), fade=True, lifetime=1)
    em.burst(50)
    assert len(em) == 5
    em.update(0.5)
    assert em.particles[0].vel.y == pytest.approx(50)
    screen = pygame.Surface((50, 50))
    em.draw(screen)
    em.shape = "square"
    em.fade = False
    em.draw(screen, camera=Camera((50, 50)))
    with pytest.raises(ValueError):
        ParticleEmitter(shape="star")
