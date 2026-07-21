import tempfile
import os
import json

from ...domain.models.document import CanonicalPage, Block

class RegionAssembler:
    """
    Assembles the region compilation context into a CanonicalPage
    """
    def assemble(self, context) -> CanonicalPage:
        blocks = []
        for rid in context.ordered_region_ids:
            box = context.regions.get(rid)
            text = context.fused_texts.get(rid, "")
            rtype = context.region_types.get(rid)
            
            blocks.append(Block(
                block_id=rid,
                content=text,
                block_type=rtype.name if hasattr(rtype, "name") else str(rtype)
            ))
            
        return CanonicalPage(
            page_number=context.page_number,
            blocks=blocks
        )
