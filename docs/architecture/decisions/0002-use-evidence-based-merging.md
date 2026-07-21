# 2. Use Evidence Based Merging

## Context
Multiple OCR providers generate overlapping bounding boxes.

## Decision
We decided to use an Evidence abstraction.

## Consequences
Allows generic spatial merging (IOU) without caring about specific provider logic.
