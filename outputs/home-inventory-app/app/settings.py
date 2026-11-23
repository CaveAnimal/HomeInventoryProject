from pathlib import Path
import os

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("HOME_INVENTORY_DATA", APP_ROOT / "data"))
PHOTO_DIR = DATA_DIR / "photos"
LABEL_DIR = DATA_DIR / "labels"
DB_PATH = Path(os.environ.get("HOME_INVENTORY_DB", DATA_DIR / "inventory.sqlite3"))
# Optional inbox for photos synced from smart glasses (e.g. Ray-Ban Meta).
# Drop images here (iCloud Photos export, USB copy, sync tool) and use the
# /import page to attach them to containers and generate item lists.
IMPORT_DIR = Path(os.environ.get("HOME_INVENTORY_IMPORT", DATA_DIR / "import-inbox"))
IMPORT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VISION_PROVIDER = os.environ.get("VISION_PROVIDER", "bonsai").lower()
# Live/mobile capture uses the fast path (Bonsai with thinking off, or
# OLLAMA_VISION_MODEL -- see vision.py). The nightly deep-scan reprocessing
# pass (app/nightly_reprocess.py) uses a slower, more thorough setting and
# re-detects items on every stored photo without blocking the capture flow.
OLLAMA_REPROCESS_VISION_MODEL = os.environ.get("OLLAMA_REPROCESS_VISION_MODEL", "qwen3-vl:30b")
# Label for the Bonsai deep scan (same model, thinking ON). Photos are
# reprocessed once per label, so changing this re-queues every photo.
BONSAI_REPROCESS_VISION_MODEL = os.environ.get("BONSAI_REPROCESS_VISION_MODEL", "bonsai2-27b-thinking")


def reprocess_vision_model() -> str:
    """Deep-scan model label for the active provider, read live from the env."""
    if os.environ.get("VISION_PROVIDER", "bonsai").lower() == "ollama":
        return os.environ.get("OLLAMA_REPROCESS_VISION_MODEL", OLLAMA_REPROCESS_VISION_MODEL)
    return os.environ.get("BONSAI_REPROCESS_VISION_MODEL", BONSAI_REPROCESS_VISION_MODEL)
# Opt-in "estimated replacement cost" lookup (see docs/AI_Planning/support/
# cost_of_replacement). Defaults to "disabled" so no network egress happens
# unless an operator explicitly opts in, matching the VISION_PROVIDER
# kill-switch precedent.
COST_LOOKUP_PROVIDER = os.environ.get("COST_LOOKUP_PROVIDER", "disabled").lower()
COST_LOOKUP_MONTHLY_LIMIT = int(os.environ.get("COST_LOOKUP_MONTHLY_LIMIT", "50"))
APP_NAME = "Home Inventory"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
