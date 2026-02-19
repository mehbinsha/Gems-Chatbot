import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytesseract
from PIL import Image, ImageOps
from backend.services.result_preference_service import ResultPreferenceService

# Use the common Windows install path when PATH is not picked up by Flask.
_default_tesseract_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if _default_tesseract_path.exists():
    pytesseract.pytesseract.tesseract_cmd = str(_default_tesseract_path)



class ResultAnalysisService:
    """Service that handles OCR extraction and subject-performance analysis."""

    # Subject aliases normalized to a canonical output name.
    SUBJECT_ALIASES = {
        "MATH": "Maths",
        "MATHS": "Maths",
        "MATHEMATICS": "Maths",
        "PHYSICS": "Physics",
        "CHEMISTRY": "Chemistry",
        "BIOLOGY": "Biology",
        "ENGLISH": "English",
        "COMPUTER": "Computer",
        "COMPUTER SCIENCE": "Computer",
        "INFORMATICS": "Computer",
        "ACCOUNTANCY": "Accountancy",
        "ECONOMICS": "Economics",
        "BUSINESS STUDIES": "Business Studies",
        "HISTORY": "History",
        "GEOGRAPHY": "Geography",
        "POLITICAL SCIENCE": "Political Science",
    }

    # OCR-friendly patterns for lines like:
    # "Maths 92", "Physics - 85/100", "English: 90"
    SUBJECT_LINE_PATTERN = re.compile(
        r"([A-Za-z][A-Za-z\s&.-]{1,40})\s*[:=\-]?\s*(\d{1,3})(?:\s*/\s*100)?\b"
    )
    NAME_PATTERN = re.compile(r"\b(?:student\s*name|name)\s*[:=\-]\s*([A-Za-z\s.]{2,60})", re.IGNORECASE)

    def analyze(self, image: Image.Image) -> Dict:
        """Run OCR and return structured result JSON-ready dict."""
        extracted_text = self._extract_text(image)
        cleaned_text = self._clean_text(extracted_text)

        name = self._extract_name(cleaned_text)
        subjects = self._extract_subject_marks(cleaned_text)

        if not subjects:
            raise ValueError("No valid subject marks were found in the uploaded result image.")

        total, average = self._calculate_summary(subjects)
        strengths = self._strongest_subjects(subjects)

        return {
            "name": name,
            "subjects": subjects,
            "total": total,
            "average": average,
            "strength_subjects": strengths,
            "recommended_courses": self._recommend_courses(average),
        }

    def _extract_text(self, image: Image.Image) -> str:
        """Preprocess image and run OCR with Tesseract."""
        # Convert to grayscale and auto-contrast for better OCR quality.
        processed = ImageOps.grayscale(image)
        processed = ImageOps.autocontrast(processed)
        return pytesseract.image_to_string(processed)

    def _clean_text(self, text: str) -> str:
        """Normalize OCR text noise so regex parsing is more reliable."""
        cleaned = text.replace("\r", "\n")
        cleaned = cleaned.replace("|", "I")
        cleaned = cleaned.replace("\u2014", "-")
        cleaned = re.sub(r"[^A-Za-z0-9:\-./\n\s]", " ", cleaned)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{2,}", "\n", cleaned)
        return cleaned.strip()

    def _extract_name(self, text: str) -> str:
        """Extract student name if present; fallback to a safe default."""
        match = self.NAME_PATTERN.search(text)
        if not match:
            return "Unknown"

        candidate = re.sub(r"\s+", " ", match.group(1)).strip()
        return candidate.title() if candidate else "Unknown"

    def _normalize_subject(self, raw_subject: str) -> str:
        """Map OCR'd subject names to canonical subject labels."""
        subject = re.sub(r"\s+", " ", raw_subject).strip().upper()
        subject = subject.replace("&", "AND")

        # Exact alias match.
        if subject in self.SUBJECT_ALIASES:
            return self.SUBJECT_ALIASES[subject]

        # Partial fallback (e.g., 'COMPUTER SCIENCE THEORY').
        for alias, canonical in self.SUBJECT_ALIASES.items():
            if alias in subject:
                return canonical

        # Keep unknown but readable subjects.
        return raw_subject.strip().title()

    def _extract_subject_marks(self, text: str) -> Dict[str, int]:
        """Extract subject->marks dictionary from cleaned OCR text."""
        subjects: Dict[str, int] = {}

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = self.SUBJECT_LINE_PATTERN.search(line)
            if not match:
                continue

            subject_raw, marks_raw = match.groups()

            # Ignore obvious non-subject metadata lines.
            if any(keyword in subject_raw.lower() for keyword in ("total", "grand", "result", "roll", "reg", "code")):
                continue

            marks = int(marks_raw)
            if marks < 0 or marks > 100:
                continue

            subject_name = self._normalize_subject(subject_raw)
            subjects[subject_name] = marks

        return subjects

    def _calculate_summary(self, subjects: Dict[str, int]) -> Tuple[int, float]:
        total = sum(subjects.values())
        average = round(total / len(subjects), 2)
        return total, average

    def _strongest_subjects(self, subjects: Dict[str, int]) -> List[str]:
        # Return top 2 subjects by score; tie-break by subject name.
        ranked = sorted(subjects.items(), key=lambda item: (-item[1], item[0]))
        return [name for name, _ in ranked[:2]]

    def _recommend_courses(self, average: float) -> List[str]:
        rules = ResultPreferenceService().get_rules()
        recommendations = ResultPreferenceService.recommend_courses(average, rules)
        if recommendations:
            return recommendations
        return ["BA English", "Hotel Management", "Arts"]
