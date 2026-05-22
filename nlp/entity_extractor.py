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
    Exhaustive deterministic mapping of mathematical and natural language comparison operators.
    Covers standard symbols, financial terminology, and logical bounds.
    """
    # Clean punctuation to ensure space boundary matching works correctly
    cleaned = re.sub(r"[.!?,\(\)\[\]\{\}\"']", " ", text.lower())
    text = f" {cleaned} "
    
    # 1. Inequality / Strict Bounds
    if any(p in text for p in [" not equal ", " != ", " differs from ", " cannot equal "]):
        return "!="
    elif any(p in text for p in [" greater than or equal ", " >= ", " at least ", " minimum ", " not less than ", " non-negative ", " non negative "]):
        return ">="
    elif any(p in text for p in [" less than or equal ", " <= ", " at most ", " maximum ", " not greater than ", " up to ", " cannot exceed ", " must not exceed ", " not exceed "]):
        return "<="
    elif any(p in text for p in [" greater than ", " > ", " over ", " exceeds ", " higher than ", " more than "]):
        return ">"
    elif any(p in text for p in [" less than ", " < ", " under ", " below ", " lower than ", " smaller than "]):
        return "<"
    elif any(p in text for p in [" equal ", " exactly ", " match ", " == ", " equals ", " identical to ", " same as "]):
        return "=="
    
    # 2. Financial / Domain Specific Fallbacks
    if " positive " in text or " > 0 " in text:
        return ">="
    elif " negative " in text or " < 0 " in text:
        return "<"
    
    return "=="  # Standard fallback

def parse_financial_number(token_text: str) -> float:
    """
    Robust financial number parser handling currency symbols, comma separators, scale suffixes (k, m),
    and written numbers like 'zero'.
    """
    clean_text = token_text.lower().strip()
    if clean_text == "zero":
        return 0.0
    clean = re.sub(r"[€$£¥,\s]", "", clean_text)
    if clean.endswith("k"):
        try: return float(clean[:-1]) * 1000.0
        except ValueError: pass
    elif clean.endswith("m"):
        try: return float(clean[:-1]) * 1000000.0
        except ValueError: pass
    try: return float(clean)
    except ValueError: return None

def extract_grammar_entities(rule_text: str) -> dict:
    """
    Uses spaCy to break down the grammar of an English rule.
    Extracts subjects (nouns), math values (numbers), and overall intent.
    """
    if not nlp:
        raise RuntimeError("spaCy is not loaded. Please ensure the model is installed.")
        
    doc = nlp(rule_text)
    lower_text = rule_text.lower()
    
    extracted = {
        "raw_text": rule_text,
        "operator": extract_operator(rule_text),
        "numbers": [],
        "subjects": [],
        "intent": "unknown"
    }
    
    # 1. Noun Chunk Extraction (Cleaning determiner stop words and punctuation)
    for chunk in doc.noun_chunks:
        clean_tokens = [t.text for t in chunk if not t.is_stop and not t.is_punct and t.pos_ in {"NOUN", "PROPN", "ADJ"}]
        clean_subj = " ".join(clean_tokens).strip()
        if clean_subj and len(clean_subj) > 1:
            extracted["subjects"].append(clean_subj.lower())
            
    # 2. Robust Financial Number Extraction
    # Scan raw regex first for formatted currency strings like "$500,000.00" or "50k" or "zero"
    matches = re.findall(r"\b(?:\d+(?:,\d{3})*(?:\.\d+)?(?:[kmKM])?|zero)\b", rule_text, re.IGNORECASE)
    for m in matches:
        val = parse_financial_number(m)
        if val is not None and val not in extracted["numbers"]:
            extracted["numbers"].append(val)
            
    # Also check spaCy tokens as backup
    if not extracted["numbers"]:
        for token in doc:
            if token.like_num:
                val = parse_financial_number(token.text)
                if val is not None and val not in extracted["numbers"]:
                    extracted["numbers"].append(val)

    # 3. Comprehensive Domain Intent Mapping
    if "if" in lower_text and any(w in lower_text for w in ["then", "must", "required"]):
        extracted["intent"] = "conditional_check"
    elif extracted["numbers"] and extracted["operator"]:
        extracted["intent"] = "numeric_comparison"
    elif any(w in lower_text for w in ["required", "must be present", "missing", "mandatory", "cannot be empty"]):
        extracted["intent"] = "required_check"
    elif any(w in lower_text for w in ["sum", "total", "calculated", "plus", "+", "added", "subtotal", "aggregation"]):
        extracted["intent"] = "calculation_check"
    elif any(w in lower_text for w in ["tax category", "tax_category", "vat category", "vat code", "tax code"]):
        extracted["intent"] = "tax_category_validation"
    elif any(w in lower_text for w in ["currency", "eur", "usd", "gbp", "jpy", "currency_code"]):
        extracted["intent"] = "currency_consistency"
    elif any(w in lower_text for w in ["date", "today", "issue_date", "due_date", "current_date", "timestamp"]):
        extracted["intent"] = "date_validation"
    elif any(w in lower_text for w in ["duplicate", "unique", "already exists", "re-submission", "resubmission"]):
        extracted["intent"] = "duplicate_check"
        
    return extracted

if __name__ == "__main__":
    # Let's run a quick internal test if you run this script directly!
    sample_rules = [
        "The total payable amount must be at least $50,000.00",
        "Every invoice ID must be mandatory",
        "Tax amount cannot exceed 50k"
    ]
    print("--- TESTING UPGRADED ENTITY EXTRACTOR ---\n")
    for rule in sample_rules:
        print(f"Rule: '{rule}'")
        res = extract_grammar_entities(rule)
        print(f"  Operator : {res['operator']}")
        print(f"  Numbers  : {res['numbers']}")
        print(f"  Subjects : {res['subjects']}")
        print(f"  Intent   : {res['intent']}\n")
