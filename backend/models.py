from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Intent(db.Model):
    __tablename__ = "intents"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(100), unique=True, nullable=False, index=True)
    patterns = db.Column(db.JSON, nullable=False, default=list)
    responses = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tag": self.tag,
            "patterns": self.patterns or [],
            "responses": self.responses or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ResultAnalysisPreference(db.Model):
    __tablename__ = "result_analysis_preferences"

    id = db.Column(db.Integer, primary_key=True)
    rules = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rules": self.rules or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ResultAnalysisHistory(db.Model):
    __tablename__ = "result_analysis_history"

    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(255), nullable=False, default="Unknown")
    total = db.Column(db.Integer, nullable=False)
    average = db.Column(db.Float, nullable=False)
    subjects = db.Column(db.JSON, nullable=False, default=dict)
    strength_subjects = db.Column(db.JSON, nullable=False, default=list)
    recommended_courses = db.Column(db.JSON, nullable=False, default=list)
    source_filename = db.Column(db.String(255), nullable=True)
    analyzed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_name": self.student_name,
            "total": self.total,
            "average": self.average,
            "subjects": self.subjects or {},
            "strength_subjects": self.strength_subjects or [],
            "recommended_courses": self.recommended_courses or [],
            "source_filename": self.source_filename,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
