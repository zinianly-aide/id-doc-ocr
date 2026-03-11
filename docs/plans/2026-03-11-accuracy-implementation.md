# Accuracy Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve extraction accuracy by documenting the SOP, separating boarding passes from train tickets, and adding a first bbox/anchor-aware boarding pass parser with regression fixtures.

**Architecture:** Keep the platform design plugin-based. Add a new `boarding_pass` plugin rather than overloading `train_ticket`, implement parser heuristics around keyword anchors and recognized line text, and route the demo pipeline through plugin-specific field extraction and validation.

**Tech Stack:** Python, pydantic, plugin registry, RapidOCR demo backend, pytest.

---

### Task 1: Add accuracy SOP documentation

**Files:**
- Create: `docs/accuracy-sop.md`
- Create: `docs/plans/2026-03-11-accuracy-implementation.md`

**Step 1: Write the document**
- Capture metrics, error taxonomy, data SOP, parser SOP, validator SOP, review-loop SOP, and roadmap.

**Step 2: Verify scope**
Run: `rg "Accuracy Improvement SOP|Weekly optimization SOP|Plugin-specific guidance" docs/accuracy-sop.md`
Expected: matching lines found.

**Step 3: Commit**
```bash
git add docs/accuracy-sop.md docs/plans/2026-03-11-accuracy-implementation.md
git commit -m "docs: add accuracy improvement sop and implementation plan"
```

### Task 2: Add boarding pass plugin skeleton

**Files:**
- Create: `src/id_doc_ocr/plugins/boarding_pass/__init__.py`
- Create: `src/id_doc_ocr/plugins/boarding_pass/plugin.py`
- Create: `src/id_doc_ocr/plugins/boarding_pass/config.yaml`
- Create: `src/id_doc_ocr/plugins/boarding_pass/label_spec.md`
- Create: `src/id_doc_ocr/plugins/boarding_pass/train_recipe.py`
- Modify: `src/id_doc_ocr/plugins/__init__.py`
- Test: `tests/test_registry.py`

**Step 1: Write the failing test**
- Extend registry test to expect `boarding_pass` registration.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_registry.py -v`
Expected: FAIL before plugin is registered.

**Step 3: Implement minimal plugin**
- Add metadata, config, and registration entry.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_registry.py -v`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/id_doc_ocr/plugins tests/test_registry.py
git commit -m "feat: add boarding pass plugin"
```

### Task 3: Add boarding pass parser and validator

**Files:**
- Create: `src/id_doc_ocr/plugins/boarding_pass/parser.py`
- Create: `src/id_doc_ocr/plugins/boarding_pass/validator.py`
- Modify: `src/id_doc_ocr/plugins/boarding_pass/plugin.py`
- Test: `tests/plugins/test_boarding_pass_parser.py`

**Step 1: Write the failing test**
- Use known OCR lines from the public boarding pass sample.

**Step 2: Run test to verify it fails**
Run: `pytest tests/plugins/test_boarding_pass_parser.py -v`
Expected: FAIL because parser does not exist.

**Step 3: Implement parser and validator**
- Extract flight number, ticket number, passenger name, date, gate, departure, arrival.
- Validate required fields and obvious conflicts.

**Step 4: Run tests to verify they pass**
Run: `pytest tests/plugins/test_boarding_pass_parser.py -v`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/id_doc_ocr/plugins/boarding_pass tests/plugins/test_boarding_pass_parser.py
git commit -m "feat: add boarding pass parser and validator"
```

### Task 4: Route demos through boarding pass plugin

**Files:**
- Create: `examples/run_boarding_pass_demo.py`
- Modify: `src/id_doc_ocr/pipeline/runner.py`
- Test: `tests/test_runner_annotation.py`

**Step 1: Write the failing test**
- Add a runner test that calls `boarding_pass` and expects parsed fields.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_runner_annotation.py -v`
Expected: FAIL before parser wiring.

**Step 3: Implement minimal wiring**
- Ensure runner uses plugin-specific `parse_fields` when available.

**Step 4: Run tests to verify they pass**
Run: `pytest tests/test_runner_annotation.py -v`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/id_doc_ocr/pipeline/runner.py examples/run_boarding_pass_demo.py tests/test_runner_annotation.py
git commit -m "feat: wire boarding pass parsing into demo runner"
```
