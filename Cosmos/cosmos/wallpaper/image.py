"""macOS static image wallpaper via AppleScript."""

from __future__ import annotations

import subprocess
from pathlib import Path


def set_image_wallpaper(image_path: str | Path) -> tuple[bool, str]:
    """Set a static image as wallpaper on all desktops using osascript."""
    path = Path(image_path).expanduser().resolve()
    if not path.is_file():
        return False, f"File not found: {path}"

    posix = str(path).replace('"', '\\"')
    script = f'''
tell application "System Events"
    repeat with d in desktops
        set picture of d to POSIX file "{posix}"
    end repeat
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "Unknown error").strip()
            return False, f"AppleScript failed: {err}"
        return True, "Wallpaper applied"
    except subprocess.TimeoutExpired:
        return False, "AppleScript timed out"
    except Exception as exc:
        return False, str(exc)


def get_current_wallpaper() -> str | None:
    """Return the POSIX path of the current desktop picture, if readable."""
    script = '''
tell application "System Events"
    return picture of desktop 1
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None
