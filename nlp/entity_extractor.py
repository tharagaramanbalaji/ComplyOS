# pyrefly: ignore [missing-import]
import spacy
import re

# Try to load the English grammar model (it might still be downloading in the background)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("Warning: spaCy model 'en_core_web_sm' is still downloading or not found.")

def extract_operator(text: str) -> str:
    """
    Deterministically maps fuzzy English phrases to strict mathematical operators.
    This replaces unpredictable LLM logic with rock-solid NLP.
    """
    text = text.lower()
    if "greater than or equal" in text or ">=" in text:
        return ">="
    elif "less than or equal" in text or "<=" in text:
        return "<="
    elif "greater than" in text or ">" in text or "over" in text:
        return ">"
    elif "less than" in text or "<" in text or "under" in text:
        return "<"
    elif "equal" in text or "exactly" in text or "match" in text or "==" in text:
        return "=="
    return "=="  # default fallback

def extract_grammar_entities(rule_text: str) -> dict:
    """
    Uses spaCy to break down the grammar of an English rule.
    Extracts subjects (nouns), math values (numbers), and overall intent.
    """
    if not nlp:
        raise RuntimeError("spaCy is not loaded. Please ensure the model is installed.")
        
    doc = nlp(rule_text)
    
    extracted = {
        "raw_text": rule_text,
        "operator": extract_operator(rule_text),
        "numbers": [],
        "subjects": [],
        "intent": "unknown"
    }
    
    # 1. Extract Noun Chunks (These are our potential JSON field names)
    # E.g., "The total payable amount" -> we extract this to send to Sentence Transformers later
    for chunk in doc.noun_chunks:
        # Clean up the subject by removing stop words like "The" or "A"
        clean_subject = " ".join([token.text for token in chunk if not token.is_stop])
        if clean_subject.strip():
            extracted["subjects"].append(clean_subject.lower())
            
    # 2. Extract Numbers (These are our target values for comparison)
    for token in doc:
        if token.like_num or re.match(r"^\d+(\.\d+)?$", token.text):
            try:
                extracted["numbers"].append(float(token.text))
            except ValueError:
                pass
                
    # 3. Detect the broad "Intent" of the rule deterministically
    lower_text = rule_text.lower()
    if "if" in lower_text and "then" in lower_text:
        extracted["intent"] = "conditional_check"
    elif "required" in lower_text or "must be present" in lower_text or "missing" in lower_text:
        extracted["intent"] = "required_check"
    elif "sum" in lower_text or "total" in lower_text or "calculated" in lower_text:
        extracted["intent"] = "calculation_check"
    elif "date" in lower_text and ("future" in lower_text or "past" in lower_text or "before" in lower_text or "after" in lower_text):
        extracted["intent"] = "date_validation"
    elif "currency" in lower_text and ("match" in lower_text or "consistent" in lower_text or "same" in lower_text):
        extracted["intent"] = "currency_consistency"
    elif "tax category" in lower_text and ("valid" in lower_text or "allowed" in lower_text or "code" in lower_text):
        extracted["intent"] = "tax_category_validation"
    elif "duplicate" in lower_text or "unique" in lower_text or "already exists" in lower_text:
        extracted["intent"] = "duplicate_check"
    elif extracted["numbers"] and extracted["operator"]:
        extracted["intent"] = "numeric_comparison"
        
    return extracted

if __name__ == "__main__":
    # Let's run a quick internal test if you run this script directly!
    sample_rule = "The total payable amount must be greater than or equal to 0"
    print(f"Testing NLP on: '{sample_rule}'\n")
    
    try:
        results = extract_grammar_entities(sample_rule)
        for key, val in results.items():
            print(f"{key.upper()}: {val}")
    except Exception as e:
        print(f"Error: {e}")
