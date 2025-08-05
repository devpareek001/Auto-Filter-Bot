import json
import os

# JSON file path - always correct regardless of where bot runs
APPROVED_FILE = os.path.join(os.path.dirname(__file__), "approved_groups.json")

def get_approved_groups():
    try:
        with open(APPROVED_FILE, "r") as f:
            data = json.load(f)
        return set(data.get("groups", []))
    except Exception:
        return set()

def approve_group_id(group_id):
    approved = get_approved_groups()
    approved.add(group_id)
    with open(APPROVED_FILE, "w") as f:
        json.dump({"groups": list(approved)}, f)
