import re
from fuzzywuzzy import process


class Normalizer:
    def __init__(self):
        # Kept in rough frequency order; short words (≤2 chars) are skipped
        # during typo correction so we don't mangle operators or short tokens.
        self.known_words = [
            "tax", "amount", "value", "amt", "charge", "invoice", "identifier",
            "number", "id", "buyer", "company", "customer", "payable", "total",
            "issue", "date", "future", "allowed", "required", "currency",
            "category", "consistent", "valid", "greater", "less", "equal",
            "exceeds", "exceed", "over", "above", "under", "below", "beyond",
            "must", "should", "cannot", "unique", "positive", "zero", "same",
            "match", "vat", "exist", "any", "with", "requires", "whenever",
            "buyer_name", "tax_amount", "tax_category", "invoice_id",
            "issue_date", "payable_amount", "then", "than", "current", "high",
            "not", "mandatory", "duplicate",
        ]

    def _correct_typos(self, text: str) -> str:
        words = text.split()
        corrected = []
        for w in words:
            # Keep operators / numbers / punctuation as-is
            if re.match(r'^[\d.><=!]+$', w):
                corrected.append(w)
                continue

            clean_w = re.sub(r'[^a-zA-Z0-9_]', '', w.lower())
            # Skip very short tokens – correcting them corrupts operators
            if not clean_w or len(clean_w) <= 2:
                corrected.append(w)
                continue

            if clean_w in self.known_words:
                corrected.append(w)
            else:
                result = process.extractOne(clean_w, self.known_words)
                if result and result[1] >= 80:
                    corrected.append(result[0])
                else:
                    corrected.append(w)
        return " ".join(corrected)

    def normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = self._correct_typos(text)

        # Natural language → operator / keyword mapping.
        # IMPORTANT: longer/guarded phrases MUST come before their shorter
        # sub-phrases to prevent partial replacement.
        op_map = [
            # ── compound phrases first (order matters!) ──────────────────
            (r"\bgreater than or equal to\b", ">="),
            (r"\bless than or equal to\b",    "<="),
            # 'should not exceed' / 'cannot exceed' BEFORE bare 'exceed'
            (r"\bshould not exceed\b",  "<="),
            (r"\bcannot exceed\b",      "<="),
            (r"\bmust not exceed\b",    "<="),
            (r"\bnot exceed\b",         "<="),
            (r"\bnot exceeding\b",      "<="),
            # ── simple operator words ────────────────────────────────────
            (r"\bgreater than\b",  ">"),
            (r"\bmore than\b",     ">"),
            (r"\babove\b",         ">"),
            (r"\bhigher than\b",   ">"),
            (r"\bexceeds\b",       ">"),
            (r"\bexceed\b",        ">"),   # bare 'exceed' AFTER guarded forms
            (r"\bless than\b",    "<"),
            (r"\bsmaller than\b", "<"),
            (r"\bunder\b",        "<"),
            (r"\bbelow\b",        "<"),
            (r"\bmust equal\b",   "=="),
            (r"\bequals\b",       "=="),
            (r"\bshould match\b", "=="),
            (r"\bmust be same as\b", "=="),
            # positive / zero
            (r"\bpositive\b",  "> 0"),
            (r"\bnon.?zero\b", "> 0"),
            (r"\bzero\b",      "0"),
            # exist / requires / mandatory → required
            (r"\bexist\b",     "required"),
            (r"\brequires\b",  "required"),
            (r"\bmandatory\b", "required"),
        ]

        for pattern, replacement in op_map:
            text = re.sub(pattern, replacement, text)

        return text
