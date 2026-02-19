# Result Analysis Module

This document describes the OCR-based result analysis flow implemented in:
- `backend/services/result_analysis_service.py`
- `backend/routes/result_routes.py`
- `backend/services/result_preference_service.py`

## Purpose

The module accepts a marksheet image, extracts text using OCR, parses subject-wise marks, computes summary metrics, and returns course recommendations.

## Request/Response Contract

Endpoint:
- `POST /analyze-result`

Input:
- `multipart/form-data`
- file field name: `file`
- allowed extensions: `.jpg`, `.jpeg`, `.png`

Success response (`200`):
```json
{
  "name": "Student Name",
  "subjects": { "Maths": 92, "Physics": 88, "English": 90 },
  "total": 270,
  "average": 90.0,
  "strength_subjects": ["Maths", "English"],
  "recommended_courses": ["Computer Science", "Engineering", "Data Science"]
}
```

Error responses:
- `400`: invalid request (missing file, unsupported extension, invalid image)
- `422`: no subject marks parsed from OCR text
- `500`: Tesseract missing or unhandled processing error

## Processing Pipeline

`ResultAnalysisService.analyze(image)` performs:

1. OCR text extraction
- converts image to grayscale
- applies autocontrast
- runs `pytesseract.image_to_string`

2. OCR text cleanup
- normalizes line breaks
- replaces noisy symbols (for example `|` -> `I`)
- strips unsupported characters
- collapses repeated spaces/newlines

3. Name extraction
- regex looks for `student name` or `name` labels
- fallback: `"Unknown"`

4. Subject/marks extraction
- scans line by line
- regex accepts common formats:
  - `Maths 92`
  - `Physics - 85/100`
  - `English: 90`
- filters non-subject lines (total, roll, reg, code, etc.)
- accepts only marks in range `0-100`

5. Subject normalization
- maps aliases to canonical names (for example `MATHEMATICS` -> `Maths`)
- handles partial alias match (for example `COMPUTER SCIENCE THEORY` -> `Computer`)

6. Summary calculation
- `total = sum(subject marks)`
- `average = round(total / subject_count, 2)`
- strongest subjects = top 2 scores (tie-break by subject name)

7. Course recommendation
- pulls rules from `ResultPreferenceService`
- returns courses where `average >= min_marks`
- fallback defaults: `["BA English", "Hotel Management", "Arts"]` if no rules match

## Subject Parsing Details

Core line pattern:

```python
([A-Za-z][A-Za-z\s&.-]{1,40})\s*[:=\-]?\s*(\d{1,3})(?:\s*/\s*100)?\b
```

This captures:
- subject label
- numeric mark (1-3 digits), optional `/100`

Important behavior:
- if the same subject appears multiple times, last matched value wins
- unknown subject names are preserved in title case

## Tesseract Dependency

The service attempts to use:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`

If this path exists, it sets `pytesseract.pytesseract.tesseract_cmd` automatically.  
If not available and not in `PATH`, requests fail with `TesseractNotFoundError`.

## Persistence

On successful analysis, the route stores one history row in `result_analysis_history` with:
- student name
- total and average
- parsed subjects
- strongest subjects
- recommended courses
- source filename
- analyzed timestamp

History can be fetched via admin API:
- `GET /api/admin/result-history?limit=50`

## Recommendation Rules Management

Rules schema:
```json
{ "course": "Computer Science", "min_marks": 85 }
```

Rules are:
- stored in `result_analysis_preferences`
- normalized and sorted by `min_marks` descending
- editable through:
  - `GET /api/admin/result-preferences`
  - `PUT /api/admin/result-preferences`

Validation constraints:
- `course`: required non-empty string
- `min_marks`: number in `[0, 100]`
