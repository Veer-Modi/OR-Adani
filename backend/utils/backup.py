"""Basic backup & restore utilities.

This is a simple, manual safety net:
- Export MongoDB collections to JSON files.
- Restore from JSON files.

Beginner note:
- This is NOT a replacement for professional backups.
- It is still useful for small deployments or quick disaster recovery.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List

from bson import json_util

from backend.database.mongo import get_db


def export_collections_to_json(output_dir: str, collections: Iterable[str]) -> List[str]:
    db = get_db()
    os.makedirs(output_dir, exist_ok=True)

    written: List[str] = []
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for name in collections:
        coll = db[name]
        docs = list(coll.find({}))

        path = os.path.join(output_dir, f"{name}_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(docs, default=json_util.default, indent=2))

        written.append(path)

    return written


def restore_collection_from_json(collection_name: str, json_path: str, drop_first: bool = False) -> Dict[str, Any]:
    db = get_db()
    coll = db[collection_name]

    with open(json_path, "r", encoding="utf-8") as f:
        raw = f.read()

    docs = json_util.loads(raw)
    if not isinstance(docs, list):
        return {"ok": False, "message": "Backup file must contain a list of documents."}

    if drop_first:
        coll.drop()

    if docs:
        coll.insert_many(docs)

    return {"ok": True, "message": f"Restored {len(docs)} documents into {collection_name}."}
