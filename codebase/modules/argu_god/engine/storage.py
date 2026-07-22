import json
import os
from datetime import datetime

DATA_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "data",
)

STATE_PATH = os.path.join(
    DATA_ROOT,
    "mindmaps",
    "local_user",
    "interaction_log.json"
)

def load_state():
    if not os.path.exists(STATE_PATH):
        return {
            "current_topic": "",
            "seen_arguments": [],
            "responses": []
        }

    with open(STATE_PATH, "r") as f:
        return json.load(f)

def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

BELIEF_PATH = os.path.join(
    DATA_ROOT,
    "mindmaps",
    "local_user",
    "belief_state.json"
)

def load_beliefs():
    if not os.path.exists(BELIEF_PATH):
        return {"arguments": {}}

    with open(BELIEF_PATH, "r") as f:
        return json.load(f)

def save_beliefs(data):
    os.makedirs(os.path.dirname(BELIEF_PATH), exist_ok=True)
    with open(BELIEF_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_response(state, argument_name, choice, custom_text):
    state["responses"].append({
        "argument": argument_name,
        "choice": choice,
        "custom_text": custom_text,
        "timestamp": datetime.now().isoformat()
    })