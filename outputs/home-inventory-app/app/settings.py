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
VISION_PROVIDER = os.environ.get("VISION_PROVIDER", "heuristic").lower()
APP_NAME = "Home Inventory"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
