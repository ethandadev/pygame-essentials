"""Keep the README honest.

1. Every ```python block in README.md that calls ``pygame.init()`` is a full
   program. Each one runs in its own process with no window, a fake clock, and
   scripted mouse clicks and key presses, and must reach the frame limit
   without crashing. The scripts in examples/ are run the same way.
2. Every "| Parameter | Default |" table must list exactly the real
   parameters of the class it documents, with the real default values.
3. Every "| Method |" / "| Property |" table may only name things that exist.
"""

import inspect
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pygame
import pytest

import pygame_toolkit as pk

README = Path(__file__).resolve().parent.parent / "README.md"
FRAMES = 150


def python_blocks():
    text = README.read_text(encoding="utf-8")
    blocks = []
    for match in re.finditer(r"```python\n(.*?)```", text, re.S):
        line = text.count("\n", 0, match.start()) + 1
        blocks.append((line, match.group(1)))
    return blocks


RUNNABLE = [(line, code) for line, code in python_blocks() if "pygame.init()" in code]
EXAMPLES = sorted((README.parent / "examples").glob("*.py"))

DRIVER = textwrap.dedent(
    """
    import os, sys
    import pygame

    FRAMES = int(sys.argv[2])
    code = open(sys.argv[1], encoding="utf-8").read()

    class FakeClock:
        def tick(self, framerate=0):
            return 16
        def get_fps(self):
            return 60.0

    pygame.time.Clock = FakeClock

    state = {"frame": 0, "pos": (400, 300), "held": set()}
    POINTS = [(x, y) for y in range(30, 600, 70) for x in range(30, 800, 110)]
    KEYS = [pygame.K_SPACE, pygame.K_e, pygame.K_h, pygame.K_j, pygame.K_x, pygame.K_p,
            pygame.K_r, pygame.K_s, pygame.K_f, pygame.K_z, pygame.K_F3, pygame.K_RETURN,
            pygame.K_BACKSPACE, pygame.K_LEFT, pygame.K_ESCAPE, pygame.K_HOME, pygame.K_ESCAPE]

    class Keys:
        def __getitem__(self, key):
            return key in state["held"]

    pygame.key.get_pressed = lambda: Keys()
    pygame.mouse.get_pos = lambda: state["pos"]
    pygame.mouse.get_pressed = lambda num_buttons=3: (False,) * num_buttons

    real_flip = pygame.display.flip

    def post(kind, **attrs):
        pygame.event.post(pygame.event.Event(kind, **attrs))

    def flip():
        f = state["frame"] = state["frame"] + 1
        pos = POINTS[(f * 7) % len(POINTS)]
        state["pos"] = pos
        post(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0))
        if f % 3 == 0:
            button = 3 if f % 21 == 0 else 1
            post(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)
            post(pygame.MOUSEBUTTONUP, pos=pos, button=button)
        if f % 11 == 0:
            post(pygame.MOUSEWHEEL, x=0, y=-1, flipped=False)
        if f % 5 == 0:
            key = KEYS[(f // 5) % len(KEYS)]
            post(pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0)
            post(pygame.KEYUP, key=key, mod=0, unicode="", scancode=0)
        if f % 4 == 0:
            post(pygame.TEXTINPUT, text="a1")
        state["held"] = ({pygame.K_RIGHT, pygame.K_d, pygame.K_s, pygame.K_SPACE}
                         if f < FRAMES // 2 else {pygame.K_LEFT, pygame.K_a, pygame.K_w, pygame.K_UP})
        if f >= FRAMES:
            post(pygame.QUIT)
        real_flip()

    pygame.display.flip = flip
    exec(compile(code, "README example", "exec"), {"__name__": "__main__"})
    print("FRAMES", state["frame"])
    """
)


def run_headless(code, label, tmp_path):
    example = tmp_path / "example.py"
    example.write_text(code, encoding="utf-8")
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER, encoding="utf-8")
    env = dict(
        os.environ,
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
        HOME=str(tmp_path),        # SaveData examples write into the temp folder
        APPDATA=str(tmp_path),
    )
    result = subprocess.run(
        [sys.executable, str(driver), str(example), str(FRAMES)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, f"{label} crashed:\n{result.stderr[-3000:]}"
    frames = re.search(r"FRAMES (\d+)", result.stdout)
    assert frames and int(frames.group(1)) >= FRAMES, f"{label} stopped early:\n{result.stdout[-2000:]}"


@pytest.mark.parametrize("line,code", RUNNABLE, ids=[f"README line {line}" for line, _ in RUNNABLE])
def test_readme_example_runs(line, code, tmp_path):
    run_headless(code, f"README example at line {line}", tmp_path)


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_folder_runs(path, tmp_path):
    run_headless(path.read_text(encoding="utf-8"), str(path.name), tmp_path)


def test_readme_has_runnable_examples():
    assert len(RUNNABLE) >= 15


# ----------------------------------------------------------- table checking
def tables_by_class():
    """Yield (class_name, header_cells, rows) for each table under a heading naming a pk export."""
    current = None
    lines = README.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            title = line.lstrip("#").strip().strip("`")
            if title in pk.__all__:
                current = title
            elif line.startswith("## "):
                current = None
        elif line.startswith("|") and current is not None:
            header = [c.strip() for c in line.strip("|").split("|")]
            rows = []
            i += 2  # skip the |---| line
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            yield current, header, rows
            continue
        i += 1


def ticked(cell):
    m = re.match(r"`([^`]*)`", cell)
    return m.group(1) if m else None


TABLES = list(tables_by_class())


def test_found_parameter_tables_for_every_class():
    documented = {name for name, header, _ in TABLES if header[:2] == ["Parameter", "Default"]}
    classes = {name for name in pk.__all__ if inspect.isclass(getattr(pk, name)) and name != "Particle"}
    assert classes <= documented, f"missing parameter tables for {classes - documented}"


@pytest.mark.parametrize(
    "name,rows",
    [(n, r) for n, h, r in TABLES if h[:2] == ["Parameter", "Default"]],
    ids=[n for n, h, _ in TABLES if h[:2] == ["Parameter", "Default"]],
)
def test_parameter_table_matches_code(name, rows):
    params = {
        (f"**{p.name}" if p.kind is p.VAR_KEYWORD else p.name): p
        for p in inspect.signature(getattr(pk, name)).parameters.values()
    }
    documented = {}
    for row in rows:
        documented[ticked(row[0])] = row[1]
    assert set(documented) == set(params), (
        f"{name}: README lists {sorted(documented)} but the code has {sorted(params)}"
    )
    for pname, default_cell in documented.items():
        p = params[pname]
        if p.kind is p.VAR_KEYWORD:
            continue
        if default_cell == "**required**":
            assert p.default is p.empty, f"{name}.{pname} is documented as required but has a default"
        else:
            expr = ticked(default_cell)
            assert expr is not None, f"{name}.{pname}: default cell should be `code`"
            assert eval(expr, {"pygame": pygame}) == p.default, (
                f"{name}.{pname}: README default {expr} != real default {p.default!r}"
            )


@pytest.mark.parametrize(
    "name,rows",
    [(n, r) for n, h, r in TABLES if h[0] in ("Method", "Property")],
    ids=[f"{n}-{h[0]}" for n, h, _ in TABLES if h[0] in ("Method", "Property")],
)
def test_method_tables_name_real_things(name, rows):
    cls = getattr(pk, name)
    for row in rows:
        member = ticked(row[0]).split("(")[0]
        assert hasattr(cls, member), f"README documents {name}.{member}, which doesn't exist"
