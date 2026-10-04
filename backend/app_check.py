"""App-check snaps (Problem 10 site testing): the website's dev-only 📸 Snap button
asks for a screenshot, and Claude takes it.

POST /api/dev/snap appends one JSON line to output/app_check_requests.jsonl.
Claude watches that file, screenshots the browser pane, saves the image under
output/app_check_images/, and records it in output/app_check_images/manifest.json
(which build_app_check.py turns into output/app_check.html).
GET /api/dev/snap/{id} tells the button whether that snap has been captured yet.

Disable with APP_CHECK=0.
"""

import json
import os
import time
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db import ROOT

OUTPUT = ROOT / "output"
REQUESTS_FILE = OUTPUT / "app_check_requests.jsonl"
MANIFEST_FILE = OUTPUT / "app_check_images" / "manifest.json"

router = APIRouter(prefix="/api/dev/snap", tags=["app check"])
ENABLED = os.getenv("APP_CHECK", "1") != "0"

CheckName = Literal["Inventory level", "Search-result cards", "Problem 9 usability feature", "Other"]


class SnapRequest(BaseModel):
    check: CheckName
    note: str = Field(default="", max_length=300)
    path: str = Field(default="/", max_length=300)


def _next_id() -> int:
    if not REQUESTS_FILE.exists():
        return 1
    return sum(1 for line in REQUESTS_FILE.read_text().splitlines() if line.strip()) + 1


@router.post("")
def request_snap(body: SnapRequest) -> dict:
    if not ENABLED:
        raise HTTPException(404, "App check is turned off.")
    OUTPUT.mkdir(exist_ok=True)
    snap = {"id": _next_id(), "check": body.check, "note": body.note.strip(), "path": body.path, "requested_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with REQUESTS_FILE.open("a") as f:
        f.write(json.dumps(snap) + "\n")
    return snap


@router.get("/{snap_id}")
def snap_status(snap_id: int) -> dict:
    if not ENABLED:
        raise HTTPException(404, "App check is turned off.")
    entries = json.loads(MANIFEST_FILE.read_text()) if MANIFEST_FILE.exists() else []
    done = next((e for e in entries if e.get("id") == snap_id), None)
    return {"id": snap_id, "captured": done is not None, "image": done["image"] if done else None}
