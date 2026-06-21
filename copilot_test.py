#!/usr/bin/env python3
"""
copilot_test.py
Improved: safer subprocess usage, clearer functions, logging, and better error handling.

Behavior:
- On Linux, tries /proc/uptime first.
- Otherwise, tries `uptime -p` if available.
- Falls back to running `uptime` and parsing its output.

This version replaces any use of os.popen() with subprocess.run(), adds
timeouts, validates that external commands exist before invoking them, and
returns sensible messages on errors.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from typing import Optional

# Configure basic logging. Users can adjust level via environment or higher-level app.
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5  # seconds for external commands


def format_seconds(seconds: float) -> str:
    """Format seconds as a human-friendly duration string."""
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return ", ".join(parts)


def uptime_from_proc() -> Optional[str]:
    """Read /proc/uptime on Linux and return a formatted duration, or None."""
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as f:
            contents = f.read().strip()
        if not contents:
            logger.debug("/proc/uptime is empty")
            return None
        uptime_seconds = float(contents.split()[0])
        return format_seconds(uptime_seconds)
    except FileNotFoundError:
        logger.debug("/proc/uptime not found on this system")
        return None
    except PermissionError:
        logger.warning("Permission denied reading /proc/uptime")
        return None
    except (ValueError, IndexError) as exc:
        logger.exception("Unexpected contents in /proc/uptime: %s", exc)
        return None
    except Exception:
        logger.exception("Unhandled error while reading /proc/uptime")
        return None


def run_command(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Run a command safely and return (returncode, stdout, stderr).

    This centralizes subprocess.run calls so callers can set timeouts and
    handle exceptions consistently.
    """
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out: %s", " ".join(cmd))
        return 124, "", "timeout"
    except FileNotFoundError:
        logger.debug("Command not found: %s", cmd[0] if cmd else "(empty)")
        return 127, "", "not found"
    except Exception:
        logger.exception("Unexpected error running command: %s", cmd)
        return 1, "", "error"


def uptime_from_uptime_p() -> Optional[str]:
    """Try `uptime -p` which prints a pretty uptime ("up 1 hour, 2 minutes")."""
    if shutil.which("uptime") is None:
        logger.debug("`uptime` command not available in PATH")
        return None
    rc, out, err = run_command(["uptime", "-p"])
    if rc != 0:
        logger.debug("`uptime -p` failed rc=%s err=%s", rc, err)
        return None
    if not out:
        return None
    # uptime -p prints "up ..." on many systems
    if out.lower().startswith("up "):
        return out[3:]
    return out


def uptime_from_uptime() -> str:
    """Run `uptime` and try to extract the human-friendly part.

    Returns a descriptive string even on failure.
    """
    if shutil.which("uptime") is None:
        logger.debug("`uptime` command not available in PATH")
        return "(uptime command not available)"

    rc, out, err = run_command(["uptime"])
    if rc != 0 or not out:
        logger.debug("`uptime` command failed rc=%s err=%s", rc, err)
        return "(could not determine uptime)"

    # Try to extract the "up ..." segment. This is typically between "up" and "load average".
    m = re.search(r"\bup\b\s+(.*?)(?:,\s+load average|\s+load averages|$)", out, flags=re.IGNORECASE)
    if m:
        candidate = m.group(1).strip().rstrip(',')
        if candidate:
            return candidate
    # If the output looks like "HH:MM:SS up 1 day,  3:45,  load average..." sometimes the up section ends with a comma
    # As a last resort, return the full output (safe, non-empty)
    return out


def main() -> int:
    """Program entry point. Returns exit code."""
    # Prefer /proc/uptime on Linux
    uptime = uptime_from_proc()
    if uptime:
        print(f"System uptime: {uptime}")
        return 0

    # Try pretty uptime
    uptime = uptime_from_uptime_p()
    if uptime:
        print(f"System uptime: {uptime}")
        return 0

    # Fallback to parsing `uptime`
    uptime = uptime_from_uptime()
    print(f"System uptime: {uptime}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
