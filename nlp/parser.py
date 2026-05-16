from nlp.entity_extractor import extract_grammar_entities
from nlp.semantic_mapper import SemanticMapper
import uuid
import json

class NLPRuleParser:
    def __init__(self):
        print("Initializing ComplyOS NLP Parser Engine...")
        # Load the heavy Sentence Transformer model once into memory
        self.mapper = SemanticMapper()

    def parse_rule(self, english_text: str) -> dict:
        """
        The master pipeline. Takes fuzzy English text and outputs 
        deterministic JSON Intermediate Representation (IR).
        """
        # STEP 1: Grammar Extraction (spaCy)
        # Pulls out mathematical intent, operators, and raw subjects
        grammar = extract_grammar_entities(english_text)
        
        intent = grammar.get("intent", "unknown")
        operator = grammar.get("operator", "==")
        numbers = grammar.get("numbers", [])
        subjects = grammar.get("subjects", [])
        
        # STEP 2: Semantic Mapping (Sentence Transformers)
        # We need to map the fuzzy spaCy subjects to our strict database schema
        primary_field = None
        if subjects:
            # Map the primary noun phrase
            mapping_result = self.mapper.map_subject_to_field(subjects[0])
            primary_field = mapping_result["mapped_field"]
        else:
            # If spaCy couldn't find a clean noun, map the whole sentence as a fallback
            mapping_result = self.mapper.map_subject_to_field(english_text)
            primary_field = mapping_result["mapped_field"]

        # STEP 3: Construct the strict JSON IR based on Intent
        ir = {
            "rule_type": "unknown", # default
        }
        
        if intent == "required_check":
            ir["rule_type"] = "required_field"
            ir["field"] = primary_field
            ir["check"] = "is_present"
            
        elif intent == "numeric_comparison":
            ir["rule_type"] = "numeric_comparison"
            ir["field"] = primary_field
            ir["operator"] = operator
            ir["value"] = numbers[0] if numbers else 0.0
            
        elif intent == "calculation_check":
            ir["rule_type"] = "amount_calculation"
            # Hardcoded heuristic for MVP to demonstrate mapping
            ir["field"] = "line_items[*].amount"
            ir["aggregation"] = "sum"
            if len(subjects) > 1:
                # If they mentioned two things, map the second thing to the expected match
                match2 = self.mapper.map_subject_to_field(subjects[1])
                ir["expected_match"] = match2["mapped_field"]
            else:
                ir["expected_match"] = primary_field
                
        else:
            # Fallback for the MVP parser
            ir["rule_type"] = "required_field"
            ir["field"] = primary_field
            ir["check"] = "is_present"

        return ir

if __name__ == "__main__":
    parser = NLPRuleParser()
    print("\n" + "="*60)
    print("--- FINAL PIPELINE: ENGLISH -> NLP -> JSON IR ---")
    print("="*60)
    
    test_sentences = [
        "The value added taxes must be present",
        "The final amount you have to pay must be greater than or equal to 100",
        "The sum of the item prices must match the base amount"
    ]
    
    for sentence in test_sentences:
        print(f"\n--- USER RAW TEXT: \"{sentence}\"")
        try:
            json_ir = parser.parse_rule(sentence)
            print("--- AUTO-GENERATED JSON IR:")
            print(json.dumps(json_ir, indent=2))
        except Exception as e:
            print(f"Error parsing: {e}")
