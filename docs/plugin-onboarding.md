# Plugin Onboarding Guide

A new document type should be added as a plugin under `src/id_doc_ocr/plugins/<plugin_name>/`.

## Required files

- `plugin.py` — plugin metadata and registration object
- `config.yaml` — default field and routing config
- `label_spec.md` — annotation instructions for humans
- `train_recipe.py` — baseline training recipe

## Recommended files

- `schema.py` — structured field definitions
- `parser.py` — post-processing logic
- `validator.py` — business rule validation
- `fixtures/` — minimal regression examples

## Onboarding steps

1. create plugin folder
2. define structured schema
3. define field list and quality rules
4. write label spec
5. add train recipe
6. register plugin in `src/id_doc_ocr/plugins/__init__.py`
7. add fixtures and tests

## Design rules

- keep plugin logic document-specific
- keep backbone logic out of plugins
- validation should be explicit and testable
- label specs must define corner cases and ambiguity policy
