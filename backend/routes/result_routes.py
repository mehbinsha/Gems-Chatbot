from flask import Blueprint, jsonify, request
from PIL import Image, UnidentifiedImageError
import pytesseract

from backend.extensions import db
from backend.models import ResultAnalysisHistory
from backend.services.result_analysis_service import ResultAnalysisService


result_bp = Blueprint("result", __name__)
analysis_service = ResultAnalysisService()
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def _is_allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@result_bp.route("/analyze-result", methods=["POST"])
def analyze_result():
    """Accept result image upload and return parsed analysis as JSON."""
    if "file" not in request.files:
        return jsonify({"error": "No file part found. Use form field name 'file'."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not _is_allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only JPG and PNG are allowed."}), 400

    try:
        image = Image.open(file.stream)
        result = analysis_service.analyze(image)
        history = ResultAnalysisHistory(
            student_name=result.get("name", "Unknown"),
            total=int(result.get("total", 0)),
            average=float(result.get("average", 0)),
            subjects=result.get("subjects", {}),
            strength_subjects=result.get("strength_subjects", []),
            recommended_courses=result.get("recommended_courses", []),
            source_filename=file.filename,
        )
        db.session.add(history)
        db.session.commit()
        return jsonify(result), 200
    except UnidentifiedImageError:
        return jsonify({"error": "Uploaded file is not a valid image."}), 400
    except pytesseract.TesseractNotFoundError:
        return jsonify({"error": "Tesseract OCR is not installed or not available in PATH."}), 500
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception:
        return jsonify({"error": "Failed to process the uploaded result image."}), 500
