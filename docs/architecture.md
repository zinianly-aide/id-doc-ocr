# Architecture

## 1. Design principles

This project is built for **identity document recognition**, not generic OCR demos.

Core principles:

1. **Deterministic first, generative second**
   - Prefer template-based and field-based extraction for stable documents.
   - Use VLM / KIE models as fallback or enhancement layers.

2. **Field accuracy over page text quality**
   - Optimize for exact match on name, ID number, birth date, expiry date, MRZ, etc.

3. **Validation is a first-class stage**
   - OCR output without business validation is not production-ready.

4. **Human review is part of the system**
   - Low-confidence or rule-conflicting outputs should be routed to review.

---

## 2. End-to-end pipeline

```text
Input image / scan
  -> document detection
  -> corner detection / segmentation
  -> geometric rectification
  -> image quality scoring
  -> document type classification
  -> template routing or adaptive layout routing
  -> field ROI extraction
  -> field OCR / MRZ / barcode decoding
  -> KIE / VLM fallback for missing fields
  -> validation and cross-field consistency checks
  -> confidence aggregation
  -> structured output or human review queue
```

---

## 3. Module breakdown

### 3.1 detector

Responsibilities:
- detect document presence
- detect document boundaries / corners
- classify coarse document family

Inputs:
- raw image

Outputs:
- bounding box
- corner points
- coarse document type
- detector confidence

### 3.2 rectify

Responsibilities:
- perspective correction
- orientation normalization
- blur / glare / occlusion checks
- quality scoring

Outputs:
- rectified image
- quality report

### 3.3 ocr

Responsibilities:
- field-level OCR adapters
- full-page OCR when needed
- specialized recognizers for machine-readable zones

Primary strategy:
- use deterministic field OCR for known templates
- use region fallback OCR when field OCR is weak

### 3.4 kie

Responsibilities:
- weak-template extraction
- free-form key-value extraction
- multimodal fallback for unseen document variants

Primary candidates:
- PaddleOCR-VL
- GOT-OCR 2.0 as regional fallback

### 3.5 validator

Responsibilities:
- document-type-specific validation rules
- date normalization and legality checks
- ID number checksum / regex checks
- MRZ parsing and checksum validation
- cross-field consistency

This stage decides whether output is:
- accepted
- accepted with warnings
- rejected to human review

### 3.6 review

Responsibilities:
- surface uncertain fields
- provide evidence boxes and candidate values
- support human correction and feedback collection

### 3.7 pipeline

Responsibilities:
- compose stages
- manage confidence thresholds
- log intermediate artifacts
- emit structured results

---

## 4. Recommended model strategy

### Production baseline

Use a **specialized pipeline** instead of a single giant OCR model:

- detector / corner model
- PaddleOCR backbone for OCR
- template-based ROI extraction
- MRZ / barcode specialized decoders
- validation engine
- VLM fallback only when deterministic path is insufficient

### Why

For ID documents, production quality usually depends more on:
- image normalization
- field routing
- validation
- confidence control

than on raw page-level OCR benchmarks alone.

---

## 5. Initial supported document families

### Phase 1
- China Resident Identity Card
- Passport with MRZ
- Driver License (schema-first, parser later)

### Later
- Residence permit
- Hong Kong / Macau / Taiwan permits
- foreign IDs and licenses

---

## 6. Data strategy

Evaluation must be field-oriented.

Primary metrics:
- field exact match
- document number exact match
- date exact match
- MRZ line exact match
- end-to-end structured extraction success rate
- manual review rate

Stress sets should include:
- blur
- glare
- perspective distortion
- cropping
- low light
- mixed language
- multiple generations / templates

---

## 7. Interfaces

Key internal objects:
- `DocumentDetection`
- `RectifiedDocument`
- `OCRFieldResult`
- `StructuredDocument`
- `ValidationReport`
- `ReviewDecision`

These will be implemented in `schemas/` first so modules can evolve independently.
