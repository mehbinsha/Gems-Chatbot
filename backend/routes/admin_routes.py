from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
import re

from backend.extensions import db
from backend.models import AdminUser, Intent
from backend.services.intent_service import IntentService
from backend.models import ResultAnalysisHistory
from backend.services.result_preference_service import ResultPreferenceService

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
intent_service = IntentService()
result_pref_service = ResultPreferenceService()


def _validate_intent_payload(payload: dict) -> tuple[bool, str]:
    tag = (payload.get("tag") or "").strip()
    patterns = payload.get("patterns")
    responses = payload.get("responses")

    if not tag:
        return False, "Tag is required."
    if not isinstance(patterns, list) or not all(isinstance(x, str) for x in patterns):
        return False, "Patterns must be a list of strings."
    if not isinstance(responses, list) or not all(isinstance(x, str) for x in responses):
        return False, "Responses must be a list of strings."
    if not responses:
        return False, "At least one response is required."

    return True, ""


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", (value or "").strip().lower()).strip("_")
    return slug or "intent"


def _build_unique_tag(base_tag: str, intent_id: int | None = None) -> str:
    candidate = base_tag
    index = 1
    while True:
        q = Intent.query.filter(Intent.tag == candidate)
        if intent_id is not None:
            q = q.filter(Intent.id != intent_id)
        if not q.first():
            return candidate
        index += 1
        candidate = f"{base_tag}_{index}"


def _generate_patterns(topic: str, details: str) -> list[str]:
    topic = (topic or "").strip()
    details = (details or "").strip()

    base_patterns = [
        topic,
        f"tell me about {topic}",
        f"what is {topic}",
        f"details about {topic}",
        f"information about {topic}",
    ]

    keywords = []
    for token in re.split(r"[,\n]", details):
        cleaned = token.strip()
        if cleaned and cleaned.lower() not in {x.lower() for x in keywords}:
            keywords.append(cleaned)

    keyword_patterns = []
    for kw in keywords[:8]:
        keyword_patterns.extend(
            [
                kw,
                f"tell me about {kw}",
                f"{topic} {kw}",
            ]
        )

    combined = [x.strip() for x in (base_patterns + keyword_patterns) if x.strip()]
    deduped = []
    seen = set()
    for pattern in combined:
        k = pattern.lower()
        if k not in seen:
            seen.add(k)
            deduped.append(pattern)
    return deduped


def _validate_smart_payload(payload: dict) -> tuple[bool, str]:
    topic = (payload.get("topic") or "").strip()
    details = (payload.get("details") or "").strip()
    responses = payload.get("responses")

    if not topic:
        return False, "Topic is required."
    if not details:
        return False, "Details are required."
    if not isinstance(responses, list) or not all(isinstance(x, str) for x in responses):
        return False, "Responses must be a list of strings."
    if not [x.strip() for x in responses]:
        return False, "At least one response is required."
    return True, ""


def _validate_result_rules(payload: dict) -> tuple[bool, str]:
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        return False, "Rules must be a non-empty list."

    for idx, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            return False, f"Rule {idx} must be an object."
        if "course" not in rule or "min_marks" not in rule:
            return False, f"Rule {idx} must include course and min_marks."

        course = str(rule.get("course", "")).strip()
        if not course:
            return False, f"Rule {idx} must include a valid course name."

        try:
            min_marks = float(rule["min_marks"])
        except (TypeError, ValueError):
            return False, f"Rule {idx} has invalid min marks."

        if min_marks < 0 or min_marks > 100:
            return False, f"Rule {idx} min marks must be between 0 and 100."

    return True, ""


@admin_bp.route("/auth/login", methods=["POST"])
def admin_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = AdminUser.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials."}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "email": user.email}), 200


@admin_bp.route("/intents", methods=["GET"])
@jwt_required()
def list_intents():
    return jsonify({"intents": intent_service.get_intents()}), 200


@admin_bp.route("/intents", methods=["POST"])
@jwt_required()
def create_intent():
    payload = request.get_json(silent=True) or {}
    ok, message = _validate_intent_payload(payload)
    if not ok:
        return jsonify({"error": message}), 400

    tag = payload["tag"].strip()
    existing = Intent.query.filter_by(tag=tag).first()
    if existing:
        return jsonify({"error": "Tag already exists."}), 409

    intent = Intent(
        tag=tag,
        patterns=[x.strip() for x in payload["patterns"] if x.strip()],
        responses=[x.strip() for x in payload["responses"] if x.strip()],
    )
    db.session.add(intent)
    db.session.commit()
    return jsonify({"intent": intent.to_dict()}), 201


@admin_bp.route("/intents/smart", methods=["POST"])
@jwt_required()
def create_intent_smart():
    payload = request.get_json(silent=True) or {}
    ok, message = _validate_smart_payload(payload)
    if not ok:
        return jsonify({"error": message}), 400

    topic = payload["topic"].strip()
    details = payload["details"].strip()
    responses = [x.strip() for x in payload["responses"] if x.strip()]

    tag = _build_unique_tag(_slugify(topic))
    patterns = _generate_patterns(topic, details)
    intent = Intent(tag=tag, patterns=patterns, responses=responses)
    db.session.add(intent)
    db.session.commit()
    return jsonify({"intent": intent.to_dict(), "generated": {"tag": tag, "patterns": patterns}}), 201


@admin_bp.route("/intents/<int:intent_id>", methods=["PUT"])
@jwt_required()
def update_intent(intent_id: int):
    payload = request.get_json(silent=True) or {}
    ok, message = _validate_intent_payload(payload)
    if not ok:
        return jsonify({"error": message}), 400

    intent = Intent.query.get_or_404(intent_id)
    tag = payload["tag"].strip()
    duplicate = Intent.query.filter(Intent.tag == tag, Intent.id != intent_id).first()
    if duplicate:
        return jsonify({"error": "Tag already exists."}), 409

    intent.tag = tag
    intent.patterns = [x.strip() for x in payload["patterns"] if x.strip()]
    intent.responses = [x.strip() for x in payload["responses"] if x.strip()]
    db.session.commit()
    return jsonify({"intent": intent.to_dict()}), 200


@admin_bp.route("/intents/<int:intent_id>/smart", methods=["PUT"])
@jwt_required()
def update_intent_smart(intent_id: int):
    payload = request.get_json(silent=True) or {}
    ok, message = _validate_smart_payload(payload)
    if not ok:
        return jsonify({"error": message}), 400

    intent = Intent.query.get_or_404(intent_id)
    topic = payload["topic"].strip()
    details = payload["details"].strip()
    responses = [x.strip() for x in payload["responses"] if x.strip()]

    tag = _build_unique_tag(_slugify(topic), intent_id=intent_id)
    patterns = _generate_patterns(topic, details)

    intent.tag = tag
    intent.patterns = patterns
    intent.responses = responses
    db.session.commit()
    return jsonify({"intent": intent.to_dict(), "generated": {"tag": tag, "patterns": patterns}}), 200


@admin_bp.route("/intents/<int:intent_id>", methods=["DELETE"])
@jwt_required()
def delete_intent(intent_id: int):
    intent = Intent.query.get_or_404(intent_id)
    db.session.delete(intent)
    db.session.commit()
    return jsonify({"message": "Intent deleted."}), 200


@admin_bp.route("/intents/<int:intent_id>/preview", methods=["GET"])
@jwt_required()
def preview_intent(intent_id: int):
    return jsonify({"preview": intent_service.preview_intent(intent_id)}), 200


@admin_bp.route("/result-preferences", methods=["GET"])
@jwt_required()
def get_result_preferences():
    rules = result_pref_service.get_rules()
    return jsonify({"rules": rules}), 200


@admin_bp.route("/result-preferences", methods=["PUT"])
@jwt_required()
def update_result_preferences():
    payload = request.get_json(silent=True) or {}
    ok, message = _validate_result_rules(payload)
    if not ok:
        return jsonify({"error": message}), 400

    pref = result_pref_service.update_rules(payload["rules"])
    return jsonify(pref.to_dict()), 200


@admin_bp.route("/result-history", methods=["GET"])
@jwt_required()
def get_result_history():
    limit_raw = request.args.get("limit", "50")
    try:
        limit = max(1, min(200, int(limit_raw)))
    except ValueError:
        limit = 50

    rows = (
        ResultAnalysisHistory.query.order_by(ResultAnalysisHistory.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"items": [x.to_dict() for x in rows]}), 200
