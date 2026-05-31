"""Background library persistence and management."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cosmos.config import (
    DATA_FILE,
    LIBRARY_DIR,
    SUPPORTED_EXTENSIONS,
    THUMBNAILS_DIR,
    ensure_dirs,
    media_type_for_path,
)
from cosmos.library.thumbnails import generate_thumbnail


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LibraryManager:
    """Manage imported wallpapers, metadata, and thumbnails."""

    def __init__(self) -> None:
        ensure_dirs()
        self._items: list[dict] = []
        self._load()

    def _load(self) -> None:
        if DATA_FILE.exists():
            try:
                data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                self._items = data.get("items", [])
            except (json.JSONDecodeError, OSError):
                self._items = []
        else:
            self._items = []

    def _save(self) -> None:
        ensure_dirs()
        payload = {"version": 1, "items": self._items}
        DATA_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_items(self) -> list[dict]:
        return list(self._items)

    def get_item(self, item_id: str) -> dict | None:
        for item in self._items:
            if item["id"] == item_id:
                return item
        return None

    def import_file(self, source_path: str) -> tuple[bool, dict | None, str]:
        src = Path(source_path).expanduser().resolve()
        if not src.is_file():
            return False, None, "File not found"

        ext = src.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return False, None, f"Unsupported file type: {ext}"

        try:
            media_type = media_type_for_path(src)
        except ValueError as exc:
            return False, None, str(exc)

        item_id = str(uuid.uuid4())
        dest_name = f"{item_id}{ext}"
        dest_path = LIBRARY_DIR / dest_name
        thumb_path = THUMBNAILS_DIR / f"{item_id}.jpg"

        try:
            shutil.copy2(src, dest_path)
            generate_thumbnail(dest_path, thumb_path)
        except OSError as exc:
            return False, None, f"Import failed: {exc}"

        item = {
            "id": item_id,
            "name": src.stem,
            "filename": dest_name,
            "path": str(dest_path),
            "thumbnail": str(thumb_path),
            "type": media_type,
            "extension": ext,
            "importedAt": _now_iso(),
            "sizeBytes": dest_path.stat().st_size,
        }
        self._items.insert(0, item)
        self._save()
        return True, self._serialize_item(item), "Imported successfully"

    def remove_item(self, item_id: str) -> tuple[bool, str]:
        item = self.get_item(item_id)
        if not item:
            return False, "Item not found"

        for path_key in ("path", "thumbnail"):
            p = Path(item[path_key])
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

        self._items = [i for i in self._items if i["id"] != item_id]
        self._save()
        return True, "Removed from library"

    def rename_item(self, item_id: str, new_name: str) -> tuple[bool, dict | None, str]:
        item = self.get_item(item_id)
        if not item:
            return False, None, "Item not found"
        name = new_name.strip()
        if not name:
            return False, None, "Name cannot be empty"
        item["name"] = name
        self._save()
        return True, self._serialize_item(item), "Renamed"

    @staticmethod
    def _serialize_item(item: dict) -> dict:
        thumb = Path(item["thumbnail"])
        return {
            "id": item["id"],
            "name": item["name"],
            "type": item["type"],
            "extension": item["extension"],
            "importedAt": item["importedAt"],
            "sizeBytes": item["sizeBytes"],
            "path": item["path"],
            "thumbnailUrl": thumb.as_uri() if thumb.exists() else "",
        }

    def serialize_all(self) -> list[dict]:
        return [self._serialize_item(i) for i in self._items]
