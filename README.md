# pygame-kit

Well-documented building blocks for [pygame](https://www.pygame.org) games. You get UI widgets, timers, sprite animation, a camera, particles, save data and a debug overlay, and **you keep your own game loop**.

```python
import pygame_kit as pk
```

Every class has detailed docstrings with examples. Hover over one in your editor, or run `help(pk.Button)`.

![UI demo](https://raw.githubusercontent.com/ethandadev/pygame-kit/main/docs/ui_demo.png)

## Install

```bash
pip install git+https://github.com/ethandadev/pygame-kit
```

Needs Python 3.9+ and pygame 2.5+.

**For working on pygame-kit itself:**

```bash
git clone https://github.com/ethandadev/pygame-kit
cd pygame-kit
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## The pattern

Everything plugs into a normal pygame loop with the same few calls:

```python
import pygame
import pygame_kit as pk

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

play = pk.Button((400, 300), size=(200, 60), text="Play", anchor="center",
                 border_radius=12, on_click=lambda: print("Let's go!"))

running = True
while running:
    dt = clock.tick(60) / 1000          # seconds since last frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        play.handle_event(event)        # 1. give it events

    play.update(dt)                     # 2. update once per frame

    screen.fill("white")
    play.draw(screen)                   # 3. draw it
    pygame.display.flip()
```

## What's inside

| | Class | What it's for |
|---|---|---|
| **UI** | `Button` | Colored or image buttons. A click counts once, on release. Use `on_click` or `was_clicked()` |
| | `Label` | Text you can change with `label.text = ...`, and it only re-renders when needed |
| | `TextInput` | Click and type, with cursor, placeholder, `max_length`, `allowed_chars`, and `on_submit` |
| | `Slider` | Drag to pick a number, with `min_value`/`max_value`/`step` and `on_change` |
| | `Checkbox`, `Toggle` | On/off controls with labels. `Toggle` slides smoothly |
| | `Dropdown` | Pick one option from a list, with scrolling for long lists |
| | `ProgressBar` | Health/loading bars, with smooth fill and a "damage trail" effect |
| **Time** | `Timer` | "Do this after X seconds", once or repeating |
| | `Cooldown` | "Only allow this every X seconds": `if cd.use(): shoot()` |
| **Graphics** | `Spritesheet` | Cut a grid image into frames, with `scale` for pixel art |
| | `Animation`, `AnimationSet` | Play frames at a set FPS, and switch between idle/run/jump |
| | `Camera` | Smooth follow, level limits, deadzone, screen shake, and world↔screen conversion |
| | `ParticleEmitter` | Sparks, dust, smoke, and trails from bursts or continuous emission |
| **Extras** | `SaveData` | A dict that saves itself to JSON, with `set_max` for high scores |
| | `DebugOverlay` | Press F3 for FPS, mouse position, watched values, and hitboxes |

## Examples

### UI

```python
name = pk.TextInput((20, 20), size=(240, 40), placeholder="Your name",
                    max_length=16, on_submit=lambda text: print("Hi", text))
volume = pk.Slider((20, 90), size=(200, 8), value=0.8,
                   on_change=pygame.mixer.music.set_volume)
music = pk.Toggle((20, 120), label="Music", checked=True)
quality = pk.Dropdown((20, 170), ["Low", "Medium", "High"], selected_index=1)
health = pk.ProgressBar((20, 240), size=(200, 18), smooth=True, trail_color=(255, 220, 120))

health.set_from(player_hp, max_hp)
```

Put the dropdown's `handle_event` **first** and its `draw` **last**, so the open list sits on top of everything else.

### Timers and cooldowns

```python
spawner = pk.Timer(2.0, spawn_enemy, repeat=True)
dash = pk.Cooldown(1.5)

# every frame
spawner.update(dt)
dash.update(dt)
if keys[pygame.K_LSHIFT] and dash.use():
    player.dash()
```

### Animation

```python
sheet = pk.Spritesheet("player.png", 16, 16, scale=3)
anims = pk.AnimationSet({
    "idle": pk.Animation(sheet.frames(row=0), fps=6),
    "run":  pk.Animation(sheet.frames(row=1), fps=12),
})

anims.play("run" if moving else "idle")   # safe to call every frame
anims.update(dt)
screen.blit(anims.image, player.rect)
```

### Camera

```python
camera = pk.Camera(screen.get_size(), world_rect=level_rect, follow_speed=8)
camera.follow(player.rect)

camera.update(dt)
screen.blit(player.image, camera.apply(player.rect))
if hit:
    camera.shake(8, 0.3)
world_mouse = camera.to_world(pygame.mouse.get_pos())
```

### Particles

```python
sparks = pk.ParticleEmitter(colors=["gold", "orange"], speed=(80, 260),
                            lifetime=(0.3, 0.7), gravity=(0, 400))
sparks.burst(40, pos=enemy.rect.center)

sparks.update(dt)
sparks.draw(screen, camera)   # camera is optional
```

### Save data

```python
save = pk.SaveData("MyGame", defaults={"highscore": 0})
if save.set_max("highscore", score):
    print("New record!")
print(save.path)   # where the file lives
```

### Debug overlay

```python
debug = pk.DebugOverlay()                     # F3 toggles
debug.watch("velocity", lambda: player.vel)

debug.handle_event(event)
debug.update(dt)
debug.draw_rect(enemy.rect)                   # hitboxes
debug.draw(screen, camera)                    # draw last
```

## Demos

```bash
python examples/ui_demo.py          # every UI widget
python examples/platformer_demo.py  # camera, animation, particles, cooldowns, save data, F3 debug
```

![Platformer demo](https://raw.githubusercontent.com/ethandadev/pygame-kit/main/docs/platformer.png)

## License

MIT © 2026 ethandadev
