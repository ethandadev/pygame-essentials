"""Works out which pygame is installed, so problems give a helpful message instead of a confusing crash.

pygame-essentials works with both **pygame-ce** (recommended, installed by
default) and classic **pygame**. The two can't be installed at the same time:
both put their files in the same ``pygame`` folder, so having both leads to
missing features and strange crashes. Importing pygame-essentials checks for
that and warns you with the exact commands to fix it.
"""

from __future__ import annotations

import warnings
from typing import Optional

try:
    from importlib import metadata as _metadata
except ImportError:  # pragma: no cover - Python < 3.8
    _metadata = None  # type: ignore[assignment]

FIX_COMMANDS = "pip uninstall -y pygame pygame-ce\n    pip install pygame-ce"


def installed_version(distribution: str) -> Optional[str]:
    """The installed version of a pip package, or ``None`` if it isn't installed."""
    if _metadata is None:
        return None
    try:
        return _metadata.version(distribution)
    except _metadata.PackageNotFoundError:
        return None


def check_pygame():
    """Import pygame, raising or warning with a clear explanation if the install is broken.

    Returns:
        The imported ``pygame`` module.

    Raises:
        ImportError: If neither pygame-ce nor pygame is installed.
    """
    try:
        import pygame
    except ImportError as exc:
        raise ImportError(
            "pygame-essentials needs pygame-ce (or classic pygame), but neither is installed.\n"
            "Install it with:\n    pip install pygame-ce"
        ) from exc

    ce_version = installed_version("pygame-ce")
    classic_version = installed_version("pygame")
    if ce_version and classic_version:
        warnings.warn(
            f"Both pygame-ce {ce_version} and pygame {classic_version} are installed. They share the "
            "same 'pygame' folder, which causes missing features and strange crashes. "
            f"Keep just one. To use pygame-ce (recommended), run:\n    {FIX_COMMANDS}",
            RuntimeWarning,
            stacklevel=2,
        )
    return pygame


def pygame_description() -> str:
    """A short description of the running pygame, like ``"pygame-ce 2.5.8"`` or ``"pygame 2.6.1"``."""
    import pygame

    name = "pygame-ce" if getattr(pygame, "IS_CE", False) else "pygame"
    return f"{name} {pygame.version.ver}"
