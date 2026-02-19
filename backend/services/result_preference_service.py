from backend.extensions import db
from backend.models import ResultAnalysisPreference


DEFAULT_RULES = [
    {"course": "Computer Science", "min_marks": 85},
    {"course": "Engineering", "min_marks": 80},
    {"course": "Data Science", "min_marks": 78},
    {"course": "BCA", "min_marks": 75},
    {"course": "BBA", "min_marks": 72},
    {"course": "Commerce", "min_marks": 70},
    {"course": "BA English", "min_marks": 60},
    {"course": "Hotel Management", "min_marks": 55},
    {"course": "Arts", "min_marks": 50},
]


class ResultPreferenceService:
    @classmethod
    def normalize_rules(cls, rules: list[dict] | None) -> list[dict]:
        if not isinstance(rules, list):
            return [dict(rule) for rule in DEFAULT_RULES]

        normalized: dict[str, dict] = {}

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            # Current schema: one course with a minimum mark.
            if "course" in rule and "min_marks" in rule:
                course = str(rule.get("course", "")).strip()
                if not course:
                    continue
                try:
                    min_marks = float(rule.get("min_marks"))
                except (TypeError, ValueError):
                    continue
                if min_marks < 0 or min_marks > 100:
                    continue
                key = course.lower()
                existing = normalized.get(key)
                if not existing or min_marks > float(existing["min_marks"]):
                    normalized[key] = {"course": course, "min_marks": min_marks}
                continue

            # Backward compatibility for old range-based schema.
            if "min_average" in rule and "courses" in rule:
                try:
                    min_marks = float(rule.get("min_average"))
                except (TypeError, ValueError):
                    continue
                if min_marks < 0 or min_marks > 100:
                    continue

                courses = rule.get("courses") or []
                if not isinstance(courses, list):
                    continue
                for course_name in courses:
                    course = str(course_name).strip()
                    if not course:
                        continue
                    key = course.lower()
                    existing = normalized.get(key)
                    if not existing or min_marks > float(existing["min_marks"]):
                        normalized[key] = {"course": course, "min_marks": min_marks}

        if not normalized:
            return [dict(rule) for rule in DEFAULT_RULES]

        ordered = sorted(
            normalized.values(),
            key=lambda item: (-item["min_marks"], item["course"]),
        )

        result = []
        for item in ordered:
            marks = item["min_marks"]
            result.append(
                {
                    "course": item["course"],
                    "min_marks": int(marks) if float(marks).is_integer() else round(marks, 2),
                }
            )
        return result

    def get_or_create(self) -> ResultAnalysisPreference:
        pref = ResultAnalysisPreference.query.order_by(ResultAnalysisPreference.id.asc()).first()
        if pref:
            normalized = self.normalize_rules(pref.rules)
            if pref.rules != normalized:
                pref.rules = normalized
                db.session.commit()
            return pref

        pref = ResultAnalysisPreference(rules=DEFAULT_RULES)
        db.session.add(pref)
        db.session.commit()
        return pref

    def get_rules(self) -> list[dict]:
        pref = self.get_or_create()
        return pref.rules or [dict(rule) for rule in DEFAULT_RULES]

    def update_rules(self, rules: list[dict]) -> ResultAnalysisPreference:
        pref = self.get_or_create()
        pref.rules = self.normalize_rules(rules)
        db.session.commit()
        return pref

    @staticmethod
    def recommend_courses(average: float, rules: list[dict]) -> list[str]:
        normalized_rules = ResultPreferenceService.normalize_rules(rules)
        eligible = []

        for rule in normalized_rules:
            min_marks = float(rule.get("min_marks", 0))
            if average >= min_marks:
                course = str(rule.get("course", "")).strip()
                if course:
                    eligible.append(course)

        return eligible
