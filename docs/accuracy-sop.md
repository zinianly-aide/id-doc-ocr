# Accuracy Improvement SOP

## Goal

This document defines the standard operating procedure for improving extraction accuracy in `id-doc-ocr` across identity documents, boarding passes, train tickets, medical records, hukou booklets, and future plugins.

---

## 1. North-star metrics

Track accuracy at field level rather than only OCR text quality.

### Required metrics
- field exact match
- critical field exact match
- document success rate
- review rate
- false accept rate
- latency and runtime cost

### Critical field examples
- identity number
- passport MRZ
- passenger name
- ticket number
- departure and arrival stations
- diagnosis and visit date

---

## 2. Error taxonomy

Every production miss should be bucketed into one root cause:
- detect_error
- quality_error
- ocr_error
- layout_error
- parser_error
- validator_error
- label_error
- schema_error

Optimization work should always start from this breakdown.

---

## 3. Data SOP

### Dataset layers
- golden set: high-confidence human-verified evaluation set
- train set
- validation set
- hard set: blur, glare, crop, distortion, new templates, mixed language

### Annotation requirements
- region geometry
- field value
- field-to-region relation
- quality tags
- template version
- review status

### Data quality rules
- define one canonical normalization rule per field
- reject ambiguous annotation guidelines
- hard cases should be at least 20% of working optimization set

---

## 4. Image pre-processing SOP

Before extraction:
1. detect document
2. rectify perspective
3. normalize orientation
4. remove obvious borders
5. score image quality

### Quality gates
- blur_score
- glare_score
- shadow_score
- crop_integrity_score
- occlusion_score

Use quality gates to decide normal path, enhanced path, or review path.

---

## 5. Extraction strategy SOP

Preferred priority:
1. fixed template ROI extraction
2. anchor-based layout extraction
3. VLM / KIE fallback

Use deterministic extraction first. Use generative or multimodal fallback only when deterministic path is insufficient.

---

## 6. Parser SOP

Each parser should use three stages:
1. candidate recall
2. candidate scoring
3. normalization

### Candidate recall signals
- keyword anchors
- regex matches
- spatial neighbors
- template-specific ROI
- language/script filters

### Candidate scoring signals
- text similarity
- bbox proximity to anchor
- format validity
- OCR confidence
- document variant consistency

### Normalization
- normalize dates
- normalize whitespace
- uppercase codes and identifiers when required
- strip OCR noise

---

## 7. Validator SOP

Validation is mandatory and should include:
- field format validation
- checksum validation
- enum validation
- cross-field consistency validation
- document completeness validation

Validation decisions:
- accept
- accept_with_warning
- review
- reject

---

## 8. Review-loop SOP

Every low-confidence result or rule-conflicting result should enter review.

Review UI/data should show:
- source image
- rectified image
- OCR lines
- candidate fields
- chosen fields
- validator errors
- bbox evidence

Human review output must feed:
- hard set
- parser regression cases
- validator regression cases
- template updates

---

## 9. Weekly optimization SOP

1. export top failures
2. cluster by root cause
3. pick highest-value failure type
4. add or fix tests first
5. implement smallest safe fix
6. run regression suite
7. release gradually
8. compare success rate, review rate, and false accept rate

---

## 10. Plugin-specific guidance

### Identity documents
- prioritize template routing, ROI extraction, checksum, MRZ

### Boarding pass / train ticket
- split by document variant early
- use anchor keywords and spatial extraction
- do not force one parser to handle all ticket-like documents

### Medical record
- support list and relation structures
- classify page type early
- use domain vocabulary normalization

### Hukou booklet
- classify page type first
- validate identity number and family relationships
- support multi-page merge later

---

## 11. Recommended roadmap

### P0
- split boarding pass from train ticket
- add bbox-aware parser
- add parser regression fixtures
- add failure logging
- add field-level evaluation reports

### P1
- add document classifier
- add page classifier
- add dataset import/export converters
- add review queue schema

### P2
- integrate full PaddleOCR adapter
- add PaddleOCR-VL fallback
- add field locator models
- add medical KIE training pipeline
