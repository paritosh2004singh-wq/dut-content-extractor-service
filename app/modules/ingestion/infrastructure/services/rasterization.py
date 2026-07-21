import fitz
import io
import hashlib
from typing import List
from ...domain.models.document import DocumentInput, PageImage
from ...domain.interfaces.capabilities import DocumentRasterizer
from ...domain.exceptions.core import ProviderException

class PyMuPDFRasterizer(DocumentRasterizer):
    def rasterize(self, document: DocumentInput, dpi: int = 300) -> List[PageImage]:
        page_images = []
        try:
            doc = fitz.open(stream=document.file_bytes, filetype=document.document_info.mime_type.split("/")[-1] if "/" in document.document_info.mime_type else "pdf")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=dpi)
                
                image_bytes = pix.tobytes("png")
                checksum = hashlib.sha256(image_bytes).hexdigest()
                
                page_images.append(PageImage(
                    page_number=page_num + 1,
                    image_bytes=image_bytes,
                    width=pix.width,
                    height=pix.height,
                    dpi=dpi,
                    rotation=page.rotation,
                    checksum=checksum,
                    metadata={"provider": "PyMuPDFRasterizer", "colorspace": pix.colorspace.name if pix.colorspace else None}
                ))
            doc.close()
            return page_images
        except Exception as e:
            raise ProviderException(f"Rasterization failed: {str(e)}")
