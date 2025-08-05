import json
import os

FILE_PATH = "allowed_groups.json"

def load_allowed_groups():
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as f:
            json.dump([], f)
    with open(FILE_PATH, "r") as f:
        return json.load(f)

def save_allowed_group(group_id: int):
    allowed = load_allowed_groups()
    if group_id not in allowed:
        allowed.append(group_id)
        with open(FILE_PATH, "w") as f:
            json.dump(allowed, f)

def is_group_allowed(group_id: int) -> bool:
    allowed = load_allowed_groups()
    return group_id in allowed
