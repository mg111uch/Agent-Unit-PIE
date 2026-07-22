#!/usr/bin/env python3
"""Tag a stable checkpoint: python scripts/tag_checkpoint.py <phase-name> [message]"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/tag_checkpoint.py <phase-name> [message]")
        sys.exit(1)

    phase = sys.argv[1]
    tag = f"phase-{phase}"

    if len(sys.argv) >= 3:
        message = sys.argv[2]
    else:
        message = f"Phase {phase} completed"

    result = subprocess.run(
        ["git", "tag", "-a", tag, "-m", message],
        capture_output=True, text=True, timeout=30,
        cwd=PROJECT_ROOT,
    )

    if result.returncode != 0:
        print(f"Error creating tag '{tag}': {result.stderr.strip()}")
        sys.exit(result.returncode)

    print(f"✅ Created tag '{tag}' — \"{message}\"")

    # Uncomment to push tags automatically:
    # push = subprocess.run(
    #     ["git", "push", "origin", "--tags"],
    #     capture_output=True, text=True, timeout=60,
    #     cwd=PROJECT_ROOT,
    # )
    # if push.returncode == 0:
    #     print(f"   Pushed tag '{tag}' to origin")
    # else:
    #     print(f"   Warning: tag not pushed — {push.stderr.strip()}")


if __name__ == "__main__":
    main()
