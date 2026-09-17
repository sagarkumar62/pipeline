import re
import unicodedata
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup


class ToolCleaner:
    """
    Deterministic cleaner for Tool records.
    Strips HTML, cleans Unicode, standardizes whitespace, and sanitizes input text.
    """

    @staticmethod
    def clean_text(text: Optional[str]) -> Optional[str]:
        if not text or not isinstance(text, str):
            return None

        # 1. Unicode normalization (NFKC)
        text = unicodedata.normalize("NFKC", text)

        # 2. Strip HTML tags if present
        if "<" in text and ">" in text:
            try:
                soup = BeautifulSoup(text, "html.parser")
                text = soup.get_text(separator=" ")
            except Exception:
                text = re.sub(r"<[^>]+>", " ", text)

        # 3. Strip control characters
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t", " "))

        # 4. Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text if text else None

    def clean_record(self, raw_extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans all string fields in an extracted record."""
        cleaned = dict(raw_extracted)
        cleaned["name"] = self.clean_text(raw_extracted.get("name")) or ""
        cleaned["description"] = self.clean_text(raw_extracted.get("description"))
        cleaned["company_name"] = self.clean_text(raw_extracted.get("company_name"))
        cleaned["category"] = self.clean_text(raw_extracted.get("category"))
        cleaned["pricing_model"] = self.clean_text(raw_extracted.get("pricing_model"))
        return cleaned

    clean = clean_record

