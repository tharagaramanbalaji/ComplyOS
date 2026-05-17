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
        if intent == "unknown":
            intent = self.mapper.predict_intent(english_text)
            
        operator = grammar.get("operator", "==")
        numbers = grammar.get("numbers", [])
        subjects = grammar.get("subjects", [])
        
        # STEP 2: Semantic Mapping (Sentence Transformers)
        # We need to map the fuzzy spaCy subjects to our strict database schema
        primary_field = None
        best_conf = 0.0
        
        if subjects:
            res_subj = self.mapper.map_subject_to_field(" ".join(subjects))
            if res_subj["confidence_score"] > best_conf:
                best_conf = res_subj["confidence_score"]
                primary_field = res_subj["mapped_field"]
                
        # Compare against clean sentence mapping
        clean_sent = english_text.lower().replace("must be present", "").replace("must be", "").replace("required", "").replace("the", "").strip()
        res_sent = self.mapper.map_subject_to_field(clean_sent)
        if res_sent["confidence_score"] > best_conf:
            primary_field = res_sent["mapped_field"]

        # STEP 3: Construct the strict JSON IR based on Intent
        ir = {
            "rule_type": "unknown", # default
        }
        
        if intent == "required_check":
            ir["rule_type"] = "required_field"
            ir["field"] = primary_field if primary_field else "invoice_id"
            ir["check"] = "is_present"
            
        elif intent == "numeric_comparison":
            ir["rule_type"] = "numeric_comparison"
            ir["field"] = primary_field if primary_field else "taxable_amount"
            ir["operator"] = operator
            ir["value"] = numbers[0] if numbers else 0.0
            
        elif intent == "conditional_check":
            ir["rule_type"] = "conditional_required_field"
            lower_text = english_text.lower()
            if "then" in lower_text:
                parts = lower_text.split("then")
                cond_part, act_part = parts[0], parts[1]
            elif "," in lower_text:
                parts = lower_text.split(",")
                cond_part, act_part = parts[0], parts[1]
            else:
                cond_part, act_part = lower_text, lower_text
                
            cond_subjs = [s for s in subjects if s in cond_part]
            act_subjs = [s for s in subjects if s in act_part and s not in cond_subjs]
            
            c_field = self.mapper.map_subject_to_field(cond_subjs[0])["mapped_field"] if cond_subjs else (primary_field or "tax_category")
            a_field = self.mapper.map_subject_to_field(act_subjs[0])["mapped_field"] if act_subjs else "tax_exemption_reason"
            
            import re
            m = re.search(r"'([^']+)'|\"([^\"]+)\"|equals?\s+([a-zA-Z0-9_]+)|is\s+([a-zA-Z0-9_]+)", english_text, re.IGNORECASE)
            if m:
                c_val = m.group(1) or m.group(2) or m.group(3) or m.group(4)
            elif "exempt" in lower_text or " e " in lower_text:
                c_val = "Exempt"
            elif "zero" in lower_text or " z " in lower_text:
                c_val = "Zero"
            elif "us" in lower_text:
                c_val = "US"
            else:
                c_val = "S"
                
            ir["condition"] = {"field": c_field, "operator": "==", "value": c_val}
            ir["action"] = {"field": a_field, "check": "is_present"}

        elif intent == "calculation_check":
            ir["rule_type"] = "amount_calculation"
            if "+" in english_text or "plus" in english_text.lower() or "added" in english_text.lower():
                fields = [self.mapper.map_subject_to_field(s)["mapped_field"] for s in subjects[:3]]
                while len(fields) < 3: fields.append("payable_amount" if len(fields) == 0 else "tax_amount")
                ir["field"] = fields[0]
                ir["equation"] = f"{fields[1]} + {fields[2]}"
            else:
                ir["field"] = "line_items[*].amount"
                ir["aggregation"] = "sum"
                match_subj = subjects[-1] if len(subjects) > 1 else (subjects[0] if subjects else "taxable_amount")
                ir["expected_match"] = self.mapper.map_subject_to_field(match_subj)["mapped_field"]
                
        elif intent == "date_validation":
            ir["rule_type"] = "date_validation"
            ir["field"] = primary_field if primary_field else "due_date"
            ir["operator"] = "<="
            ir["value"] = "CURRENT_DATE"
            
        elif intent == "currency_consistency":
            ir["rule_type"] = "currency_consistency"
            ir["field"] = primary_field if (primary_field and "line_item" in english_text.lower()) else "line_items[*].currency_code"
            import re
            m = re.search(r"\b([A-Z]{3})\b", english_text)
            if m:
                ir["expected_match"] = m.group(1)
            else:
                ir["expected_match"] = "currency_code"
            
        elif intent == "tax_category_validation":
            ir["rule_type"] = "tax_category_validation"
            if primary_field and "line" in english_text.lower():
                ir["field"] = "line_items[*].tax_category"
            else:
                ir["field"] = primary_field if primary_field else "tax_category"
            clean_words = [w.strip(".'\",;!?()[]{}") for w in english_text.split()]
            ignore_words = {
                "the", "tax", "category", "should", "shpuld", "must", "be", "equal", "to", 
                "in", "on", "of", "or", "as", "that", "have", "has", "is", "are", "an", "a", 
                "code", "rule", "line", "item", "items", "invoice", "doc", "document", "xml", 
                "file", "all", "any", "xyz", "check", "valid", "value", "values", "with", 
                "from", "this", "each", "only", "also", "when", "then", "than", "and", "not", 
                "for", "can", "our", "you", "we", "they", "saw", "its", "but", "why", "now", 
                "one", "two", "six", "ten", "make", "sure", "every"
            }
            codes = []
            for w in clean_words:
                if len(w) <= 4 and w.lower() not in ignore_words and w.isalpha():
                    codes.append(w.upper())
            ir["valid_values"] = list(set(codes)) if codes else ["S", "E", "Z", "AE", "K", "G", "O"]
            
        elif intent == "duplicate_check":
            ir["rule_type"] = "duplicate_field_check"
            ir["field"] = primary_field if primary_field else "invoice_id"
            ir["check"] = "is_unique_globally"

        else:
            raise ValueError("Could not mathematically parse the rule intent. Please rephrase the rule using simpler language.")

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
