# Platform Architecture

## Goal

Evolve `id-doc-ocr` from a document-specific OCR repository into a **general document recognition platform** with pluggable document adapters.

Initial document plugins:
- china_id
- passport
- medical_record
- train_ticket
- hukou_booklet

## Layered architecture

### 1. Core platform layer
Shared orchestration and contracts:
- plugin registry
- stage interfaces
- pipeline assembly
- common schemas
- confidence aggregation
- review routing

### 2. Backbone adapter layer
Model adapters that can be swapped without changing plugin logic:
- PaddleOCR
- PaddleOCR-VL
- GOT-OCR
- future detection / KIE / VLM backbones

### 3. Plugin layer
Each document family is implemented as a plugin with:
- schema
- parser
- validator
- config
- labeling spec
- training recipe
- fixtures / examples

### 4. Data & MLOps layer
Shared tooling for:
- dataset manifest management
- annotation conversion
- split generation
- training recipes
- regression evaluation
- migration / transfer learning

## Extensibility contract

A new document type should be addable by:
1. creating a new plugin directory
2. implementing the standard plugin interface
3. registering the plugin
4. adding label spec and train recipe
5. adding fixtures and eval cases

## Why this design

This keeps the repository extensible across document categories while preserving the ability to optimize deeply for each document family.
