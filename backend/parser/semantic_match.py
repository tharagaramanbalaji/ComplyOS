# Optional lightweight semantic matching
# Currently using basic fuzzy matching or exact match to avoid heavy LLM dependency
# Can be extended with sentence-transformers for paraphrase understanding

import difflib
from typing import Optional
from .template_matcher import TemplateMatcher
from schemas.schema import IRNode

class SemanticMatcher:
    def __init__(self):
        self.template_matcher = TemplateMatcher()
        # Predefined canonical phrases for paraphrase mapping
        self.canonical_rules = {
            "tax amount must be positive if tax category is provided": "If tax amount > 0 tax category required",
            "the field document currency code is mandatory": "currency is required",
            "issue date cannot be empty": "issue date cannot be in the future",
            "tax category must be valid": "tax category is valid",
            "invoice id must be unique": "invoice id is unique"
        }

    def match(self, rule_text: str) -> Optional[IRNode]:
        # Clean text
        text_lower = rule_text.lower().strip()
        
        # 1. Direct template match
        ir = self.template_matcher.match(rule_text)
        if ir:
            return ir
            
        # 2. Fuzzy match to canonical rules
        best_match = None
        highest_ratio = 0.0
        
        for canonical, transformed in self.canonical_rules.items():
            ratio = difflib.SequenceMatcher(None, text_lower, canonical).ratio()
            if ratio > 0.8 and ratio > highest_ratio:
                highest_ratio = ratio
                best_match = transformed
                
        if best_match:
            return self.template_matcher.match(best_match)
            
        return None
