# Changelog

All notable changes to pygame-essentials are listed here. Versions follow [semantic versioning](https://semver.org): `MAJOR.MINOR.PATCH`.

- **PATCH** (0.1.0 → 0.1.1): bug fixes only
- **MINOR** (0.1.0 → 0.2.0): new features, existing code keeps working
- **MAJOR** (0.x → 1.0.0): changes that can break existing code

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

[0.1.0]: https://github.com/ethandadev/pygame-essentials/releases/tag/v0.1.0
