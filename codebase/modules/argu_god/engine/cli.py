import json
import os
from argu_god.engine.loop import run_explore_loop

def argu_cli(mode: str, topic: str):
    if not mode or not topic:
        return "Usage: /argu explore <topic>"

    if mode == "explore":
        return run_explore_loop(topic)

    return f"Unsupported mode: {mode}"