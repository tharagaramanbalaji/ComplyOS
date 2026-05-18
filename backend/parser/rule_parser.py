import re
import uuid
from typing import Dict, Any, List

from schemas.schema import ParsedRule, IRNode
from .semantic_match import SemanticMatcher
from .normalizer import Normalizer
from .synonym_mapper import SynonymMapper
from .intent_classifier import IntentClassifier
from .confidence_score import ConfidenceScore


class RuleParser:
    def __init__(self):
        self.semantic_matcher = SemanticMatcher()
        self.normalizer = Normalizer()
        self.synonym_mapper = SynonymMapper()
        self.intent_classifier = IntentClassifier()
        self.confidence_score = ConfidenceScore()

    def _build_unknown_ir(self, raw_text: str) -> IRNode:
        """Return a minimal unknown node – never exposed to the API caller."""
        return IRNode(type="unknown")

    def _pipeline(self, raw_text: str) -> tuple[IRNode, dict]:
        """Run the full NLP pipeline and return (IRNode, debug_info)."""
        # Stage 1 – Normalize (typo correction + operator mapping)
        normalized = self.normalizer.normalize(raw_text)
        # Stage 2 – Synonym mapping (field name canonicalization)
        mapped = self.synonym_mapper.map_synonyms(normalized)
        # Stage 3 – Intent classification (fast heuristic routing)
        intent = self.intent_classifier.classify(mapped)
        # Stage 4 – Template / semantic matching
        ir_node = self.semantic_matcher.match(mapped)

        if ir_node is None:
            ir_node = IRNode(type=intent if intent != "unknown" else "unknown")
        elif ir_node.type == "unknown" and intent != "unknown":
            ir_node.type = intent

        confidence = self.confidence_score.calculate(mapped, intent, ir_node)

        debug = {
            "raw_input": raw_text,
            "normalized": normalized,
            "after_synonym_map": mapped,
            "intent": intent,
            "confidence": confidence,
        }
        return ir_node, debug

    def parse(
        self,
        rule_text: str,
        severity: str = "ERROR",
        expected_error: str = "",
    ) -> List[ParsedRule]:
        # Split on newlines OR a period followed by whitespace
        raw_rules = [r.strip() for r in re.split(r"\n|\.\s", rule_text) if r.strip()]

        parsed_rules: List[ParsedRule] = []
        for raw_text in raw_rules:
            ir_node, debug = self._pipeline(raw_text)
            rule_id = f"RULE-{str(uuid.uuid4())[:8].upper()}"

            parsed_rules.append(ParsedRule(
                rule_id=rule_id,
                rule_text=raw_text,
                rule_type=ir_node.type,
                severity=severity,
                expected_error_message=expected_error or f"Validation failed: {raw_text}",
                structured_IR=ir_node,
                parsed_entities=debug,
            ))

        return parsed_rules
