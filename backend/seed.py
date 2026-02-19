import json
import os

from backend.extensions import db
from backend.models import AdminUser, Intent


def seed_database(
    admin_email: str = "admin@example.com",
    admin_password: str = "Admin@12345",
    intents_json_path: str = "backend/nlp/intents.json",
) -> dict:
    if not os.path.isabs(intents_json_path):
        intents_json_path = os.path.abspath(intents_json_path)

    admin_created = False
    if not AdminUser.query.filter_by(email=admin_email).first():
        admin = AdminUser(email=admin_email)
        admin.set_password(admin_password)
        db.session.add(admin)
        admin_created = True

    added, updated = sync_intents_from_file(intents_json_path, update_existing=False)
    db.session.commit()
    return {"admin_created": admin_created, "added": added, "updated": updated}


def sync_intents_from_file(intents_json_path: str, update_existing: bool = False) -> tuple[int, int]:
    if not os.path.isabs(intents_json_path):
        intents_json_path = os.path.abspath(intents_json_path)

    with open(intents_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    added = 0
    updated = 0

    for item in data.get("intents", []):
        tag = (item.get("tag") or "").strip()
        if not tag:
            continue

        patterns = item.get("patterns", [])
        responses = item.get("responses", [])

        existing = Intent.query.filter_by(tag=tag).first()
        if existing:
            if update_existing:
                existing.patterns = patterns
                existing.responses = responses
                updated += 1
            continue

        db.session.add(Intent(tag=tag, patterns=patterns, responses=responses))
        added += 1

    return added, updated
