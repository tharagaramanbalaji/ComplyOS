import re


class SynonymMapper:
    def __init__(self):
        # Patterns ordered longest → shortest to prevent partial shadowing.
        # Each (pattern, replacement) pair uses word-boundary anchors.
        self.field_mappings = [
            (r"\b(?:tax exemption reason|exemption reason)\b",      "tax_exemption_reason"),
            (r"\b(?:tax category|tax code)\b",                      "tax_category"),
            (r"\b(?:taxable amount|taxable value|taxable base)\b",  "taxable_amount"),
            (r"\b(?:invoice identifier|invoice number|invoice id)\b","invoice_id"),
            (r"\b(?:payable amount|total payable|invoice total|total amount)\b", "payable_amount"),
            (r"\b(?:tax amount|tax value|tax amt|invoice tax|tax charge)\b",     "tax_amount"),
            (r"\b(?:invoice date|issue date)\b",                    "issue_date"),
            (r"\b(?:buyer company|buyer customer|buyer vat|buyer|customer)\b",   "buyer_name"),
            (r"\b(?:currency code|currency)\b",                     "currency_code"),
            (r"\b(?:seller name|seller|supplier)\b",                "seller_name"),
        ]

    def map_synonyms(self, text: str) -> str:
        for pattern, replacement in self.field_mappings:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
