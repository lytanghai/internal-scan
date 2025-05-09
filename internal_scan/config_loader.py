import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config.json'

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

config = load_config()
