import re


class IntentClassifier:
    """
    Heuristic intent classifier.  Runs AFTER normalizer + synonym_mapper so
    field names are already canonicalized and operators are already symbols.
    """

    def classify(self, text: str) -> str:
        t = text.lower()

        # ── conditional_required_field ────────────────────────────────────
        # "if / whenever / any invoice with <field> OP <num> <required_field>"
        if re.search(r'\b(?:if|whenever|any)\b', t) and re.search(r'[><=]', t):
            return "conditional_required_field"
        # Also catches implicit: "tax_amount >100 tax_category required"
        if re.search(r'[><=]\s*\d+.*required', t):
            return "conditional_required_field"

        # ── amount_calculation ────────────────────────────────────────────
        if "==" in t and "+" in t:
            return "amount_calculation"

        # ── date_validation ───────────────────────────────────────────────
        # Matches: "date … <=", "date … future", "date … current", "date … today"
        if re.search(r'\b(?:issue_date|date)\b', t) and (
            re.search(r'<=', t) or
            re.search(r'\b(?:future|current|today|past)\b', t) or
            re.search(r'\bnot exceed\b|\bcannot exceed\b|\bshould not exceed\b', t)
        ):
            return "date_validation"

        # ── duplicate_field_check ─────────────────────────────────────────
        if re.search(r'\b(?:unique|duplicate)\b', t):
            return "duplicate_field_check"

        # ── currency_consistency ──────────────────────────────────────────
        if re.search(r'\bcurrency\b', t) and re.search(r'\bconsistent\b', t):
            return "currency_consistency"

        # ── tax_category_validation ───────────────────────────────────────
        if re.search(r'\btax_category\b', t):
            return "tax_category_validation"

        # ── numeric_comparison ────────────────────────────────────────────
        if re.search(r'[><=]\s*\d+', t):
            return "numeric_comparison"

        # ── required_field ────────────────────────────────────────────────
        if re.search(r'\b(?:required|mandatory|must exist|cannot be empty)\b', t):
            return "required_field"

        return "unknown"
