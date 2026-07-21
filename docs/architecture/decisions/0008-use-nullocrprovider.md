# 8. Use NullOCRProvider

## Context
PaddleOCR has rigid dependencies (<= 3.13) which break in 3.14.

## Decision
We implemented the Null Object Pattern via NullOCRProvider.

## Consequences
Prevents dependency drift from crashing the orchestrator.
