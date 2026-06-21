#!/usr/bin/env python3
"""
copilot_test.py
Prints the system uptime in a human-friendly format.

Behavior:
- On Linux, tries /proc/uptime first.
- Otherwise, tries `uptime -p` if available.
- Falls back to running `uptime` and printing its output.
"""

from __future__ import annotations

import re
import subprocess
import sys


def format_seconds(seconds: float) -> str:
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


def uptime_from_proc() -> str | None:
    try:
        with open("/proc/uptime", "r") as f:
            contents = f.read().strip()
        uptime_seconds = float(contents.split()[0])
        return format_seconds(uptime_seconds)
    except Exception:
        return None


def uptime_from_uptime_p() -> str | None:
    try:
        res = subprocess.run(["uptime", "-p"], capture_output=True, text=True, check=False)
        out = res.stdout.strip()
        if out:
            # `uptime -p` prints like: "up 1 hour, 2 minutes"
            return out[3:] if out.lower().startswith("up ") else out
        return None
    except Exception:
        return None


def uptime_from_uptime() -> str:
    try:
        res = subprocess.run(["uptime"], capture_output=True, text=True, check=False)
        out = res.stdout.strip()
        if not out:
            return "(could not determine uptime)"
        # Try to extract the "up ..." part from the output
        m = re.search(r" up (.+?),?\s+load average", out)
        if m:
            return m.group(1)
        # Fallback: return whole uptime output
        return out
    except Exception:
        return "(could not determine uptime)"


def main() -> int:
    # Try /proc/uptime first (Linux)
    uptime = uptime_from_proc()
    if uptime:
        print(f"System uptime: {uptime}")
        return 0

    # Try `uptime -p`
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
