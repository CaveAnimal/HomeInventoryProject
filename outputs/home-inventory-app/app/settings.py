from pathlib import Path
import os

APP_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("HOME_INVENTORY_DATA", APP_ROOT / "data"))
PHOTO_DIR = DATA_DIR / "photos"
LABEL_DIR = DATA_DIR / "labels"
DB_PATH = Path(os.environ.get("HOME_INVENTORY_DB", DATA_DIR / "inventory.sqlite3"))
VISION_PROVIDER = os.environ.get("VISION_PROVIDER", "heuristic").lower()
APP_NAME = "Home Inventory"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
