# Changelog

All notable changes to pygame-essentials are listed here. Versions follow [semantic versioning](https://semver.org): `MAJOR.MINOR.PATCH`.

- **PATCH** (0.1.0 → 0.1.1): bug fixes only
- **MINOR** (0.1.0 → 0.2.0): new features, existing code keeps working
- **MAJOR** (0.x → 1.0.0): changes that can break existing code

## [0.2.0] - Unreleased

### Changed
- **pygame-ce is now the default.** `pip install pygame-essentials` installs `pygame-ce>=2.4` instead of classic `pygame`. You still write `import pygame`. Classic pygame 2.5+ still works: install with `pip install --no-deps pygame-essentials` (see the README).
- **Upgrading from 0.1.0:** pip won't remove the classic pygame that 0.1.0 installed, so you'd end up with both. Upgrade like this instead:
  ```bash
  pip uninstall -y pygame pygame-ce
  pip install -U pygame-essentials
  ```
- Decimal positions and sizes (like `Vector2` or `FRect.center`) are now rounded instead of cut off, so `(10.7, 20.2)` becomes `(11, 20)`.

### Added
- Python 3.14 support (thanks to pygame-ce).
- Importing pygame-essentials warns, with the exact fix, when **both** pygame and pygame-ce are installed. That clash causes missing features and strange crashes.
- A clear `ImportError` telling you to `pip install pygame-ce` when no pygame is installed.
- `DebugOverlay` shows which pygame is running, like `pygame-ce 2.5.8`.
- Tests with pygame-ce `FRect`s in `Camera` and `DebugOverlay`.

## [0.1.0] - Sept 14, 2026

First release.

### UI
- `Button`: colored or image buttons. A click fires once on release, with `on_click` or `was_clicked()`.
- `Label`: cached text that keeps its anchor point when the text changes size.
- `TextInput`: focus, cursor, scrolling, placeholder, `max_length`, `allowed_chars`, `on_submit`, `on_change`.
- `Slider`: range, step snapping, `on_change`.
- `Checkbox` and `Toggle` (animated switch).
- `Dropdown`: scrolling list that consumes clicks while open.
- `ProgressBar`: smooth fill, damage trail, custom text, color functions.
- `Widget` base class for making your own widgets, and `resolve_font`.

### Time
- `Timer`: one-shot or repeating, with pause/resume/restart.
- `Cooldown`: `use()`, `ready()`, `trigger()`, `progress`.

### Graphics
- `Spritesheet` with margin, spacing and scale.
- `Animation` (looping or one-shot, flipping) and `AnimationSet`.
- `Camera`: smooth follow, world limits, deadzone, offset, shake, world↔screen conversion.
- `ParticleEmitter`: bursts and continuous emission, gravity, drag, fade, color and size over life.

### Extras
- `SaveData`: auto-saving JSON dict in the system app-data folder, with `set_max`/`set_min` and crash-safe writes.
- `DebugOverlay`: F3 overlay with FPS, mouse position, watched values and hitboxes.

[0.2.0]: https://github.com/ethandadev/pygame-essentials/releases/tag/v0.2.0
[0.1.0]: https://github.com/ethandadev/pygame-essentials/releases/tag/v0.1.0
