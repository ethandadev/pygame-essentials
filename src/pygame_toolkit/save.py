"""Save game data (high scores, settings, unlocks) to a file with one line of code.

Data is stored as JSON in the normal place for app data on each computer,
so it survives restarting the game. It **doesn't** go next to your code,
where it could be accidentally committed or deleted:

* **macOS:** ``~/Library/Application Support/<game name>/``
* **Windows:** ``%APPDATA%\\<game name>\\``
* **Linux:** ``~/.local/share/<game name>/``

Quick example::

    save = pk.SaveData("SpaceDodger", defaults={"highscore": 0, "volume": 0.8})

    print(save["highscore"])              # 0 the first time, then whatever was saved
    if save.set_max("highscore", score):
        print("NEW HIGH SCORE!")
    save["volume"] = volume_slider.value  # saved to disk automatically
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Union


def default_save_folder(game_name: str) -> Path:
    """The standard folder for a game's save files on this computer.

    Args:
        game_name: Your game's name. It becomes the folder name.

    Returns:
        A ``Path``, like ``~/Library/Application Support/MyGame`` on a Mac. The
        folder is **not** created by this function.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / game_name


class SaveData:
    """A dictionary that saves itself to a JSON file.

    Use it like a normal dict (``save["coins"] = 10``, ``save["coins"]``,
    ``"coins" in save``). With ``autosave=True`` (the default), every change is
    written to disk right away, so progress isn't lost if the game crashes.

    Saving is **safe**: the new data is written to a temporary file first and
    then swapped in, so a crash mid-save can't leave you with a half-written,
    broken file. If the file does get broken (for example, someone edited it by
    hand), it's renamed to ``<name>.corrupt`` and you start from ``defaults``
    with a warning, instead of the game crashing.

    Args:
        game_name: Your game's name. It decides the save folder (see the module
            docs). Use the same name every time!
        filename: Name of the file inside the folder. Use different
            filenames for separate save slots, like ``"slot1.json"``.
        defaults: Starting values for keys that haven't been saved yet. They
            aren't written to the file until you change something.
        folder: Save somewhere else instead of the standard folder, for
            example ``"saves"`` for a folder next to your game.
        autosave: If True, every ``set``/``delete``/``clear`` saves
            immediately. If False, nothing is written until you call
            :meth:`save`, which is faster if you change lots of things at once.

    Attributes:
        path (pathlib.Path): Full path to the save file. Print it to find
            your save file.

    Raises:
        TypeError: When setting a value that can't be stored in JSON.

    What can be saved:
        ``str``, ``int``, ``float``, ``bool``, ``None``, and ``list``/``dict``
        made of those. **Tuples come back as lists** (JSON has no tuples), so
        ``(255, 0, 0)`` loads as ``[255, 0, 0]``. Surfaces, Rects, and your own
        classes can't be saved directly. Save their numbers instead.

    Example:
        Settings with defaults::

            settings = pk.SaveData("MyGame", filename="settings.json",
                                   defaults={"music": True, "volume": 0.7})
            music_toggle = pk.Toggle((20, 20), checked=settings["music"],
                                     on_change=lambda on: settings.set("music", on))
    """

    def __init__(
        self,
        game_name: str,
        *,
        filename: str = "save.json",
        defaults: Optional[Dict[str, Any]] = None,
        folder: Union[str, os.PathLike, None] = None,
        autosave: bool = True,
    ) -> None:
        self.game_name = game_name
        self.folder = Path(folder) if folder is not None else default_save_folder(game_name)
        self.path = self.folder / filename
        self.defaults: Dict[str, Any] = copy.deepcopy(defaults) if defaults else {}
        self.autosave = autosave
        self._data: Dict[str, Any] = {}
        self.reload()

    # --------------------------------------------------------------- file I/O
    def reload(self) -> None:
        """Throw away unsaved changes and read the file again."""
        self._data = {}
        if not self.path.exists():
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, dict):
                raise ValueError("save file doesn't contain a JSON object")
            self._data = loaded
        except (ValueError, OSError) as exc:
            broken = self.path.with_suffix(self.path.suffix + ".corrupt")
            try:
                os.replace(self.path, broken)
            except OSError:
                pass
            warnings.warn(
                f"Save file {self.path} couldn't be read ({exc}). "
                f"It was moved to {broken.name} and defaults are being used.",
                RuntimeWarning,
                stacklevel=2,
            )

    def save(self) -> None:
        """Write everything to disk now.

        You only need this if you made the SaveData with ``autosave=False``.
        """
        self.folder.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.folder, prefix=".tmp-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise

    def _changed(self) -> None:
        if self.autosave:
            self.save()

    # -------------------------------------------------------------- dict-like
    def get(self, key: str, default: Any = None) -> Any:
        """Get a saved value.

        Looks in the save file first, then in ``defaults``, then returns
        ``default``.

        Args:
            key: The name of the value, like ``"highscore"``.
            default: What to return if the key isn't saved and isn't in
                ``defaults``.

        Returns:
            A **copy** of the value, so changing a returned list doesn't
            secretly change the save. Use :meth:`set` to store changes.
        """
        if key in self._data:
            return copy.deepcopy(self._data[key])
        if key in self.defaults:
            return copy.deepcopy(self.defaults[key])
        return default

    def set(self, key: str, value: Any) -> None:
        """Store a value (and save to disk if ``autosave`` is on).

        Args:
            key: The name to store it under. Must be a string.
            value: Anything JSON can hold (see "What can be saved" above).

        Raises:
            TypeError: If ``key`` isn't a string or ``value`` can't be saved as
                JSON. The error message says what went wrong.
        """
        if not isinstance(key, str):
            raise TypeError(f"save keys must be strings (got {type(key).__name__})")
        try:
            value = json.loads(json.dumps(value))
        except (TypeError, ValueError) as exc:
            raise TypeError(
                f"can't save {key!r}: {exc}. Save numbers, strings, bools, "
                "lists or dicts instead (for a Rect, save [x, y, w, h])"
            ) from None
        self._data[key] = value
        self._changed()

    def set_max(self, key: str, value: float) -> bool:
        """Save ``value`` only if it's bigger than what's saved, which is perfect for high scores.

        Args:
            key: Like ``"highscore"``.
            value: The new score.

        Returns:
            True if it was a new record (and was saved).

        Example::

            if save.set_max("highscore", score):
                show_new_record_banner()
        """
        current = self.get(key)
        if current is None or value > current:
            self.set(key, value)
            return True
        return False

    def set_min(self, key: str, value: float) -> bool:
        """Save ``value`` only if it's smaller than what's saved, which is perfect for best times.

        Args:
            key: Like ``"best_lap_time"``.
            value: The new time.

        Returns:
            True if it was a new record (and was saved).
        """
        current = self.get(key)
        if current is None or value < current:
            self.set(key, value)
            return True
        return False

    def delete(self, key: str) -> None:
        """Remove a saved value. Afterwards, ``get`` falls back to ``defaults``.

        Doesn't complain if the key wasn't saved.
        """
        if key in self._data:
            del self._data[key]
            self._changed()

    def clear(self) -> None:
        """Erase **all** saved values, like a "Reset progress" button."""
        self._data.clear()
        self._changed()

    def has(self, key: str) -> bool:
        """True if the key is saved **or** has a default."""
        return key in self._data or key in self.defaults

    @property
    def data(self) -> Dict[str, Any]:
        """A copy of everything: defaults plus saved values."""
        merged = copy.deepcopy(self.defaults)
        merged.update(copy.deepcopy(self._data))
        return merged

    def __getitem__(self, key: str) -> Any:
        if not self.has(key):
            raise KeyError(f"{key!r} isn't saved and has no default")
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        self.delete(key)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self.has(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)

    def __repr__(self) -> str:
        return f"<SaveData {self.path}>"
