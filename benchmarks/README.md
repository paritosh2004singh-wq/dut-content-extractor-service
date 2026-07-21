# Benchmark Suite

This directory contains the regression benchmark suite for the extraction service.

## Categories
- `digital/`: Born-digital PDFs
- `scanned/`: Scanned PDFs
- `hybrid/`: PDFs containing both digital text and scanned images
- `multilingual/`: Documents in multiple languages
- `forms/`: Structured forms
- `invoices/`: Invoices and receipts
- `books/`: Large books and long-form documents
- `ieee/`: IEEE double-column academic papers
- `manuals/`: Technical manuals with complex layouts

## Tracking Metrics
- Extraction accuracy (IOU of text bounding boxes, string edit distance)
- Runtime (Total pipeline duration, Provider-specific latency)
- Confidence (Confidence scorer output accuracy)
- Merge quality (Conflict resolution correctness)
