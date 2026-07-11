
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.document import DocumentInput, DocumentPage, PageImage
from ..models.region import LayoutRegion, RecognizedText, TableResult, FigureResult, FormulaResult
from ..evidence.core import TextEvidence, TableEvidence, FigureEvidence, FormulaEvidence

class DocumentParser(ABC):
    @abstractmethod
    def parse(self, document: DocumentInput) -> List[DocumentPage]:
        pass

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image: PageImage, region: Optional[LayoutRegion] = None) -> List[RecognizedText]:
        pass

class LayoutDetector(ABC):
    @abstractmethod
    def detect_regions(self, image: PageImage) -> List[LayoutRegion]:
        pass

class TableExtractor(ABC):
    @abstractmethod
    def extract_tables(self, image: PageImage, regions: List[LayoutRegion]) -> List[TableEvidence]:
        pass

class FigureExtractor(ABC):
    @abstractmethod
    def extract_figures(self, image: PageImage, regions: List[LayoutRegion]) -> List[FigureEvidence]:
        pass

class FormulaExtractor(ABC):
    @abstractmethod
    def extract_formulas(self, image: PageImage, regions: List[LayoutRegion]) -> List[FormulaEvidence]:
        pass

class ImagePreprocessor(ABC):
    @abstractmethod
    def preprocess(self, image: PageImage) -> PageImage:
        pass
