"""Set up local data for the front end from your copy of campus_customs.db.

1. Exports the catalogue table to frontend/src/data/catalogue.json.
2. Copies product photos from data/products/ to frontend/public/products/.

Both outputs are git-ignored (they come from the private database and images).
Run from the HW4 folder after placing the data:  python3 scripts/export_catalogue.py
"""

import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
IMAGES_SRC = ROOT / "data" / "products"
OUT_PATH = ROOT / "frontend" / "src" / "data" / "catalogue.json"
IMAGES_OUT = ROOT / "frontend" / "public" / "products"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT product_id, name, garment_type, description, colors, "
        "search_tags, image_file_path, price FROM catalogue ORDER BY name"
    ).fetchall()
    conn.close()

    products = [
        {
            "productId": r["product_id"],
            "name": r["name"],
            "garmentType": r["garment_type"],
            "description": r["description"],
            "colors": json.loads(r["colors"]),
            "searchTags": json.loads(r["search_tags"]),
            "imageFilePath": r["image_file_path"],
            "price": r["price"],
        }
        for r in rows
    ]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(products, indent=2))
    print(f"Wrote {len(products)} products to {OUT_PATH.relative_to(ROOT)}")

    if IMAGES_SRC.is_dir():
        shutil.copytree(IMAGES_SRC, IMAGES_OUT, dirs_exist_ok=True)
        print(f"Copied product images to {IMAGES_OUT.relative_to(ROOT)}")
    else:
        print(f"No {IMAGES_SRC.relative_to(ROOT)} folder found; add the product photos there and re-run.")


if __name__ == "__main__":
    main()
