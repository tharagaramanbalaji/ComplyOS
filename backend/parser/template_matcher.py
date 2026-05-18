import re
from typing import Optional

from schemas.schema import IRNode


def _clean_field(text: str) -> str:
    """Strip grammatical noise and convert to snake_case field name."""
    noise = (
        r'\b(?:must be|should be|must|should|is|are|cannot be|any invoice with'
        r'|if|whenever|then|requires|required|exist|allowed|not|do)\b'
    )
    cleaned = re.sub(noise, '', text, flags=re.IGNORECASE)
    # Collapse whitespace and convert to snake_case
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    # Remove leading/trailing underscores introduced by noise removal
    cleaned = cleaned.strip('_')
    return cleaned.lower()


class TemplateMatcher:
    """
    Ordered list of regex templates.  Each template is tried in order; the
    first match wins.  All patterns operate on the *normalized + synonym-mapped*
    rule text so field names are already canonical (e.g. tax_amount, issue_date).
    """

    def __init__(self):
        self.templates = [

            # ── 1. conditional_required_field ─────────────────────────────
            # "if tax_amount > 100 tax_category required"
            # "whenever payable_amount > 10000 buyer_name required"
            # "any invoice with tax_amount > 0 tax_category required"
            {
                "pattern": (
                    r"(?:if|whenever|any\s+invoice\s+with)\b\s*"
                    r"(?P<cond_field>\w+)\s*"
                    r"(?P<op>[><=!]=?)\s*"
                    r"(?P<cond_val>\d+)\s*"
                    r",?\s*(?:then\s+)?"
                    r"(?P<req_field>.+?)\s*(?:required|is required|must exist|should exist)?\s*$"
                ),
                "type": "conditional_required_field",
                "extract": lambda m: {
                    "condition": {
                        "field": m.group("cond_field").strip(),
                        "operator": m.group("op").strip(),
                        "value": int(m.group("cond_val")),
                    },
                    "required_field": _clean_field(m.group("req_field")),
                },
            },

            # ── 2. required_field ─────────────────────────────────────────
            # "invoice_id required"  /  "invoice_id is required"
            {
                "pattern": (
                    r"^(?P<field>[\w_]+(?:\s+[\w_]+)*?)\s+"
                    r"(?:is\s+|are\s+|should\s+be\s+|must\s+be\s+)?"
                    r"(?:required|mandatory|must exist|cannot be empty)\s*$"
                ),
                "type": "required_field",
                "extract": lambda m: {
                    "field": _clean_field(m.group("field")),
                },
            },

            # ── 3. duplicate_field_check ──────────────────────────────────
            # "invoice_id unique"  /  "invoice_id must be unique"
            {
                "pattern": (
                    r"^(?P<field>[\w_]+(?:\s+[\w_]+)*?)\s+"
                    r"(?:must be\s+|should be\s+|is\s+)?unique\s*$"
                ),
                "type": "duplicate_field_check",
                "extract": lambda m: {
                    "field": _clean_field(m.group("field")),
                },
            },

            # ── 4. date_validation ───────────────────────────────
            # Matches after normalisation: 'issue_date should <= current date'
            # or before: 'issue_date cannot be future'
            {
                "pattern": (
                    r"(?:issue_date|date)\s*"
                    r"(?:"
                    r"(?:should\s+)?(?:not\s+)?<=\s*current(?:_date)?"  # normalized form
                    r"|<=\s*current(?:_date)?"                           # plain <=
                    r"|cannot be (?:in the )?future"
                    r"|must not be (?:in the )?future"
                    r"|should not (?:be )?(?:in the )?future"
                    r"|should not exceed (?:current|today)"
                    r"|cannot exceed (?:current|today)"
                    r"|must not exceed (?:current|today)"
                    r"|not exceed (?:current|today)"
                    r")"
                ),
                "type": "date_validation",
                "extract": lambda m: {
                    "field": "issue_date",
                    "operator": "<=",
                    "value": "current_date",
                },
            },

            # ── 5. numeric_comparison ─────────────────────────────────────
            # "tax_amount > 0"  /  "tax_amount should be > 0"
            {
                "pattern": (
                    r"^(?P<field>[\w_]+(?:\s+[\w_]+)*?)\s*"
                    r"(?:must be|should be|must|should|is|are)?\s*"
                    r"(?P<op>[><=!]=?)\s*"
                    r"(?P<val>\d+(?:\.\d+)?)\s*$"
                ),
                "type": "numeric_comparison",
                "extract": lambda m: {
                    "field": _clean_field(m.group("field")),
                    "operator": m.group("op").strip(),
                    "value": (int(m.group("val"))
                              if m.group("val").isdigit()
                              else float(m.group("val"))),
                },
            },

            # ── 6. amount_calculation ─────────────────────────────────────
            # "payable_amount == taxable_amount + tax_amount"
            {
                "pattern": (
                    r"^(?P<target>[\w_]+)\s*==\s*"
                    r"(?P<f1>[\w_]+)\s*\+\s*(?P<f2>[\w_]+)\s*$"
                ),
                "type": "amount_calculation",
                "extract": lambda m: {
                    "target_field": m.group("target").strip(),
                    "operator": "==",
                    "field_1": m.group("f1").strip(),
                    "field_2": m.group("f2").strip(),
                },
            },

            # ── 7. currency_consistency ───────────────────────────────────
            {
                "pattern": r"\bcurrency_code\b.*\bconsistent\b",
                "type": "currency_consistency",
                "extract": lambda m: {},
            },

            # ── 8. tax_category_validation ────────────────────────────────
            # "tax_category should be AE"  /  "tax_category required"
            {
                "pattern": (
                    r"\btax_category\b\s*"
                    r"(?:should be|must be|is|required|valid)?\s*"
                    r"(?P<val>[A-Z0-9]+)?"
                ),
                "type": "tax_category_validation",
                "extract": lambda m: {
                    "field": "tax_category",
                    "value": m.group("val") if m.group("val") else None,
                },
            },
        ]

    def match(self, rule_text: str) -> Optional[IRNode]:
        for template in self.templates:
            m = re.search(template["pattern"], rule_text, re.IGNORECASE)
            if m:
                extracted = template["extract"](m)
                # Remove None values so IRNode defaults apply cleanly
                extracted = {k: v for k, v in extracted.items() if v is not None}
                return IRNode(type=template["type"], **extracted)
        return None
