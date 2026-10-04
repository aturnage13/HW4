"""Record app-check screenshots and build output/app_check.html (Problem 10 site testing).

Record a captured snap (copies the image, updates the manifest, rebuilds the page):
    .venv/bin/python build_app_check.py add --id 1 --image /path/to/screenshot.jpg \
        --title "..." --description "..."
Just rebuild the page:
    .venv/bin/python build_app_check.py build
"""

import argparse
import html
import json
import re
import shutil
import time

from app_check import MANIFEST_FILE, OUTPUT, REQUESTS_FILE

IMAGES_DIR = MANIFEST_FILE.parent
PAGE = OUTPUT / "app_check.html"
REQUIRED = ["Inventory level", "Search-result cards", "Problem 9 usability feature"]


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def requests_by_id() -> dict[int, dict]:
    if not REQUESTS_FILE.exists():
        return {}
    rows = [json.loads(line) for line in REQUESTS_FILE.read_text().splitlines() if line.strip()]
    return {r["id"]: r for r in rows}


def add(snap_id: int, image: str, title: str, description: str, check: str | None) -> None:
    request = requests_by_id().get(snap_id, {})
    check = check or request.get("check", "Other")
    slug = re.sub(r"[^a-z0-9]+", "-", f"{check} {title}".lower()).strip("-")[:60]
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    dest = IMAGES_DIR / f"{snap_id:02d}-{slug}.jpg"
    shutil.copyfile(image, dest)

    entries = [e for e in load(MANIFEST_FILE, []) if e["id"] != snap_id]
    entries.append({
        "id": snap_id,
        "check": check,
        "title": title,
        "description": description,
        "image": f"app_check_images/{dest.name}",
        "page": request.get("path", ""),
        "note": request.get("note", ""),
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    entries.sort(key=lambda e: e["id"])
    MANIFEST_FILE.write_text(json.dumps(entries, indent=2))
    build()
    print(f"Saved {dest.relative_to(OUTPUT.parent)} and rebuilt {PAGE.relative_to(OUTPUT.parent)}")


def build() -> None:
    entries = load(MANIFEST_FILE, [])
    e = html.escape

    rows = []
    for check in REQUIRED:
        hits = [x for x in entries if x["check"] == check]
        links = ", ".join(f'<a href="#snap-{x["id"]}">Snap {x["id"]}</a>' for x in hits)
        status = "Covered" if hits else "Not yet captured"
        rows.append(
            f'<tr><td>{e(check)}</td><td class="{"pass" if hits else "todo"}">{status}</td><td>{links or "—"}</td></tr>'
        )

    sections = []
    for x in entries:
        note = f"<dt>Tester's note</dt><dd>{e(x['note'])}</dd>" if x.get("note") else ""
        sections.append(f"""
    <section class="check" id="snap-{x['id']}" data-check="{e(x['check'])}">
      <h2>Snap {x['id']}: {e(x['check'])}: {e(x['title'])}</h2>
      <dl>
        <dt>Check</dt><dd>{e(x['check'])}</dd>
        <dt>Page</dt><dd><code>{e(x['page'] or '—')}</code></dd>
        <dt>Captured</dt><dd>{e(x['captured_at'])}</dd>{note}
      </dl>
      <figure>
        <img src="{e(x['image'])}" alt="Screenshot for {e(x['check'])}: {e(x['title'])}">
        <figcaption><strong>What this shows:</strong> {e(x['description'])}</figcaption>
      </figure>
    </section>""")

    PAGE.write_text(f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Campus Customs App Check</title>
  <style>
    body {{ font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; color: #1a1f2b; background: #f5f6f8; margin: 0; line-height: 1.5; }}
    header {{ background: #00356b; color: #fff; padding: 1.5rem 1rem; }}
    header h1 {{ margin: 0 0 .25rem; }}
    main {{ max-width: 1000px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    th, td {{ border: 1px solid #dde1e6; padding: .5rem .75rem; text-align: left; }}
    th {{ background: #eceef1; }}
    td.pass {{ color: #1d6b3a; font-weight: 700; }}
    td.todo {{ color: #a12121; font-weight: 700; }}
    .check {{ background: #fff; border: 1px solid #dde1e6; border-radius: 10px; padding: 1rem 1.25rem; margin: 1.5rem 0; }}
    .check h2 {{ margin-top: 0; font-size: 1.2rem; color: #00356b; }}
    dl {{ display: grid; grid-template-columns: max-content 1fr; gap: .25rem 1rem; margin: 0 0 1rem; }}
    dt {{ font-weight: 700; }}
    dd {{ margin: 0; }}
    figure {{ margin: 0; }}
    img {{ width: 100%; height: auto; border: 1px solid #dde1e6; border-radius: 6px; }}
    figcaption {{ margin-top: .5rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Campus Customs App Check</h1>
    <div>Site testing screenshots taken live while the tester used the site (Homework 4, Problem 10).</div>
  </header>
  <main>
    <h2>Required checks</h2>
    <table>
      <thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
    <p>Each snap below lists the check it covers, the page it was taken on, the screenshot, and what it shows. Screenshots are in <code>app_check_images/</code>.</p>
    {''.join(sections) or '<p><em>No screenshots captured yet.</em></p>'}
  </main>
</body>
</html>
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--id", type=int, required=True)
    a.add_argument("--image", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--description", required=True)
    a.add_argument("--check")
    sub.add_parser("build")
    args = parser.parse_args()
    if args.cmd == "add":
        add(args.id, args.image, args.title, args.description, args.check)
    else:
        build()
