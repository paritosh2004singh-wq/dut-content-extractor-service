from typing import List, Dict, Tuple
from ...domain.evidence.core import (
    Evidence, TextEvidence, TableEvidence, TableRow, TableCell, TextLine
)
from ...domain.models.document import DocumentPage
from ...domain.context.metrics import QualityMetrics
from ...domain.value_objects.confidence import ConfidenceScore

class ConfidenceScorer:
    """
    Rolls up ConfidenceScores from cell -> row -> table -> page -> document.
    Calculates overall Document quality metrics.
    """

    def score_document(self, pages: List[DocumentPage]) -> QualityMetrics:
        if not pages:
            return QualityMetrics(overall_confidence=0.0)

        page_confidences: Dict[int, float] = {}
        region_confidences: Dict[str, float] = {}
        
        total_doc_score = 0.0
        total_doc_weight = 0.0

        for page in pages:
            page_score, page_weight, page_regions = self._score_page(page)
            
            if page_weight > 0:
                avg_page_conf = page_score / page_weight
                page_confidences[page.page_number] = avg_page_conf
                total_doc_score += page_score
                total_doc_weight += page_weight
            else:
                page_confidences[page.page_number] = 0.0

            region_confidences.update(page_regions)

        overall = total_doc_score / total_doc_weight if total_doc_weight > 0 else 0.0

        return QualityMetrics(
            overall_confidence=overall,
            page_confidences=page_confidences,
            region_confidences=region_confidences
        )

    def _score_page(self, page: DocumentPage) -> Tuple[float, float, Dict[str, float]]:
        total_page_score = 0.0
        total_page_weight = 0.0
        region_confidences: Dict[str, float] = {}

        for ev in page.evidence:
            score, weight = self._score_evidence(ev)
            if weight > 0:
                total_page_score += score
                total_page_weight += weight
                region_confidences[ev.evidence_id] = score / weight
            else:
                region_confidences[ev.evidence_id] = 0.0

        return total_page_score, total_page_weight, region_confidences

    def _score_evidence(self, ev: Evidence) -> Tuple[float, float]:
        if isinstance(ev, TableEvidence):
            return self._score_table(ev)
        elif isinstance(ev, TextEvidence):
            return self._score_text(ev)
        
        # Base fallback
        if ev.confidence:
            return ev.confidence.score, 1.0
        return 0.0, 0.0

    def _score_table(self, table: TableEvidence) -> Tuple[float, float]:
        total_score = 0.0
        total_weight = 0.0

        for row in table.rows:
            row_score, row_weight = self._score_row(row)
            if row_weight > 0:
                total_score += row_score
                total_weight += row_weight

        # If table itself has a confidence but no rows/cells had confidence, use it
        if total_weight == 0 and table.confidence:
            return table.confidence.score, 1.0

        return total_score, total_weight

    def _score_row(self, row: TableRow) -> Tuple[float, float]:
        total_score = 0.0
        total_weight = 0.0

        for cell in row.cells:
            cell_score, cell_weight = self._score_cell(cell)
            if cell_weight > 0:
                total_score += cell_score
                total_weight += cell_weight

        if total_weight == 0 and row.confidence:
            return row.confidence.score, 1.0

        return total_score, total_weight

    def _score_cell(self, cell: TableCell) -> Tuple[float, float]:
        if cell.confidence:
            # We could weight by cell content length
            weight = len(cell.text) if cell.text else 1.0
            return cell.confidence.score * weight, weight
        return 0.0, 0.0

    def _score_text(self, text_ev: TextEvidence) -> Tuple[float, float]:
        total_score = 0.0
        total_weight = 0.0

        for line in text_ev.lines:
            if line.confidence:
                weight = len(line.text) if line.text else 1.0
                total_score += line.confidence.score * weight
                total_weight += weight

        if total_weight == 0 and text_ev.confidence:
            weight = len(text_ev.text) if text_ev.text else 1.0
            return text_ev.confidence.score * weight, weight

        return total_score, total_weight
