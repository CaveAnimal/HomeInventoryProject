from pathlib import Path

import qrcode

from ..settings import LABEL_DIR


def generate_qr(public_id: str, box_name: str, target_url: str) -> str:
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{public_id}.png"
    path = LABEL_DIR / filename
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(target_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(path)
    return filename


def label_path(filename: str) -> Path:
    return LABEL_DIR / filename
