import json
import time
from pathlib import Path

CACHE_FILE = Path(__file__).resolve().parent.parent / 'cache.json'

def set_cache(key, value, ttl=86400):
    cache = _load_cache()
    cache[key] = {
        "value": value,
        "expires_at": time.time() + ttl
    }
    _save_cache(cache)
    print('cache saved successfully')

def get_cache(key):
    cache = _load_cache()
    if key in cache:
        entry = cache[key]
        if time.time() < entry["expires_at"]:
            return entry["value"]
        else:
            del cache[key]  # Expired
            _save_cache(cache)
    return None

def _load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _save_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
