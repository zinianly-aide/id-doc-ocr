# 2026-03-11 Platform Design

## Decision
Use a **general document platform + vertical adapters** architecture.

## Scope expansion
In addition to identity documents, the repository will support:
- medical records
- train tickets
- hukou booklet

## Core requirements
- strong extensibility
- portable data format
- model-agnostic backbone adapters
- unified labeling / training / evaluation toolchain
- plugin-based document onboarding

## Next implementation tracks
1. plugin registry and contracts
2. document plugin skeletons
3. internal dataset manifest format
4. training / eval / conversion tool skeleton
5. first runnable CLI / demos
