import logging
import unicodedata
from collections import Counter

from ...domain.interfaces.classification import IScriptDetector
from ...domain.value_objects.enums import ScriptType

logger = logging.getLogger(__name__)

# Unicode script name -> our ScriptType mapping
UNICODE_SCRIPT_MAP = {
    "LATIN": ScriptType.LATIN,
    "DEVANAGARI": ScriptType.DEVANAGARI,
    "ARABIC": ScriptType.ARABIC,
    "CJK": ScriptType.HAN,
    "HAN": ScriptType.HAN,
    "CYRILLIC": ScriptType.CYRILLIC,
    "HIRAGANA": ScriptType.KANA,
    "KATAKANA": ScriptType.KANA,
    "HANGUL": ScriptType.HANGUL,
    "THAI": ScriptType.THAI,
    "TAMIL": ScriptType.TAMIL,
    "TELUGU": ScriptType.TELUGU,
}


def _classify_char_script(char: str) -> str:
    """
    Returns the Unicode script category for a single character.
    Uses unicodedata.name() to infer the script block.
    """
    if char.isspace() or char in ".,;:!?()[]{}\"'-/\\@#$%^&*+=<>~`|_":
        return "COMMON"
    try:
        name = unicodedata.name(char, "")
    except ValueError:
        return "UNKNOWN"

    # Unicode character names start with the script block name
    for script_key in UNICODE_SCRIPT_MAP:
        if name.startswith(script_key):
            return script_key

    # CJK Unified Ideographs
    if "CJK" in name:
        return "HAN"

    if name.startswith("DIGIT") or name.startswith("FULL"):
        return "COMMON"

    return "UNKNOWN"


class UnicodeScriptDetector(IScriptDetector):
    """
    Script detector that analyzes the Unicode codepoints of text
    already extracted by Docling's native text layer.

    This is a pre-OCR heuristic: Docling often extracts partial text
    during layout analysis. We use that text to vote on the dominant
    script, which then drives OCR provider routing.

    For image-only regions (no text), falls back to UNKNOWN and lets
    the RoutingEngine use BEST_CONFIDENCE policy.
    """

    def __init__(self):
        # region_id -> text snippet cache, populated during layout
        self._region_texts: dict[str, str] = {}

    def register_text(self, region_id: str, text: str):
        """
        Called by DoclingLayoutAnalyzer to cache text for each region.
        """
        self._region_texts[region_id] = text

    def detect_script(self, region_id: str) -> ScriptType:
        text = self._region_texts.get(region_id, "")

        if not text or len(text.strip()) < 3:
            logger.info(f"ScriptDetector[Instrumented]: region {region_id} has insufficient native text (len={len(text)}), returning UNKNOWN")
            return ScriptType.UNKNOWN

        # Count script votes across all characters
        votes: Counter = Counter()
        for ch in text:
            script = _classify_char_script(ch)
            if script != "COMMON" and script != "UNKNOWN":
                votes[script] += 1

        if not votes:
            logger.info(f"ScriptDetector: region {region_id} produced no script votes, returning UNKNOWN")
            return ScriptType.UNKNOWN

        dominant_script, count = votes.most_common(1)[0]
        total_meaningful = sum(votes.values())
        ratio = count / total_meaningful if total_meaningful > 0 else 0

        result = UNICODE_SCRIPT_MAP.get(dominant_script, ScriptType.UNKNOWN)

        logger.info(
            f"ScriptDetector: region {region_id} -> {result} "
            f"(dominant={dominant_script}, ratio={ratio:.2f}, votes={dict(votes)})"
        )
        return result

    def clear(self):
        """Clear cache to prevent memory leaks across documents."""
        self._region_texts.clear()
