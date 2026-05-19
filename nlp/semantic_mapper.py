import re

class SemanticMapper:
    def __init__(self):
        print("Initializing lightweight ComplyOS Semantic Mapper Engine...")
        self.field_descriptions = {
            "invoice_id": "the unique identifier number of the invoice",
            "issue_date": "the date the invoice was issued or created",
            "seller_name": "the name of the seller or vendor",
            "buyer_name": "the name of the buyer or customer",
            "currency_code": "the main currency code like USD or EUR",
            "taxable_amount": "the base taxable amount before taxes",
            "tax_amount": "the total tax amount, value added taxes, or VAT",
            "payable_amount": "the total final payable amount including taxes",
            "tax_category": "the tax category code like S or E",
            "tax_exemption_reason": "the reason for tax exemption",
            "line_items[*].amount": "the individual price amount of a single line item product",
            "line_items[*].currency_code": "the currency of a single line item",
            "line_items[*].tax_category": "the tax category of a single line item"
        }
        self.corpus_keys = list(self.field_descriptions.keys())

    def map_subject_to_field(self, extracted_subject: str) -> dict:
        """
        Maps fuzzy English subjects to strict JSON database fields using a highly optimized,
        lightweight lexical overlap algorithm to fit within the 512MB RAM Render Free Tier.
        """
        subject_lower = extracted_subject.lower()
        # Clean text
        subject_clean = re.sub(r'[^\w\s]', ' ', subject_lower)
        words = set(subject_clean.split())
        
        # Word lists mapping concepts to target fields
        synonyms = {
            "invoice_id": {"invoice", "id", "identifier", "number", "invoice_id", "id_invoice"},
            "issue_date": {"issue", "date", "created", "creation", "issued", "issue_date", "invoice_date"},
            "due_date": {"due", "date", "payment", "deadline", "due_date", "pay_date"},
            "seller_name": {"seller", "name", "vendor", "seller_name"},
            "buyer_name": {"buyer", "name", "customer", "buyer_name", "receiver"},
            "currency_code": {"currency", "code", "currency_code", "usd", "eur", "gbp", "main_currency"},
            "taxable_amount": {"taxable", "amount", "base", "before", "taxable_amount"},
            "tax_amount": {"tax", "amount", "vat", "value", "added", "tax_amount"},
            "payable_amount": {"payable", "amount", "total", "final", "pay", "payable_amount", "sum"},
            "tax_category": {"tax", "category", "code", "tax_category"},
            "tax_exemption_reason": {"exemption", "reason", "exempt", "tax_exemption_reason"},
            "line_items[*].amount": {"line", "item", "amount", "price", "product"},
            "line_items[*].currency_code": {"line", "item", "currency", "code"},
            "line_items[*].tax_category": {"line", "item", "tax", "category", "code"}
        }
        
        best_field = None
        best_score = -1.0
        
        # Check if subject mentions line item
        is_line = any(w in words for w in ["line", "item", "product", "price"])
        
        for field, field_syns in synonyms.items():
            # Guide mapping based on line-item context
            if is_line and not field.startswith("line_items"):
                continue
            if not is_line and field.startswith("line_items"):
                continue
                
            # Compute intersection-over-union-like match score
            intersection = words.intersection(field_syns)
            if not intersection:
                score = 0.0
            else:
                score = len(intersection) / len(words.union(field_syns))
                
            if score > best_score:
                best_score = score
                best_field = field
                
        # Default fallbacks if no match
        if best_score <= 0.0:
            if is_line:
                best_field = "line_items[*].amount"
            else:
                best_field = "invoice_id"
            best_score = 0.5
            
        return {
            "mapped_field": best_field,
            "confidence_score": best_score,
            "original_subject": extracted_subject
        }

    def predict_intent(self, rule_text: str) -> str:
        """
        Predicts rule intent using lightweight keyword routing to avoid PyTorch loading.
        """
        lower_text = rule_text.lower()
        if "if" in lower_text and any(w in lower_text for w in ["then", "must", "required"]):
            return "conditional_check"
        elif any(w in lower_text for w in ["sum", "total", "calculated", "plus", "+", "added", "subtotal", "aggregation", "equals"]):
            return "calculation_check"
        elif any(w in lower_text for w in ["tax category", "tax_category", "vat category", "vat code", "tax code", "tax_code"]):
            return "tax_category_validation"
        elif any(w in lower_text for w in ["currency", "eur", "usd", "gbp", "jpy", "currency_code"]):
            return "currency_consistency"
        elif any(w in lower_text for w in ["date", "today", "issue_date", "due_date", "current_date", "timestamp"]):
            return "date_validation"
        elif any(w in lower_text for w in ["duplicate", "unique", "already exists", "re-submission", "resubmission"]):
            return "duplicate_check"
        elif any(w in lower_text for w in ["at least", "minimum", "maximum", "greater", "less", "more than", "positive", "negative", "equal", "==", ">=", "<="]):
            return "numeric_comparison"
        elif any(w in lower_text for w in ["required", "must be present", "missing", "mandatory", "cannot be empty", "should contain"]):
            return "required_check"
        else:
            return "required_check"  # Default fallback

if __name__ == "__main__":
    mapper = SemanticMapper()
    test_phrases = [
        "the final amount you have to pay",
        "value added taxes",
        "date of invoice creation",
        "the price of an individual product"
    ]
    for phrase in test_phrases:
        result = mapper.map_subject_to_field(phrase)
        print(f"User Subject : '{phrase}'")
        print(f"Mapped Field : {result['mapped_field']}")
        print(f"Confidence   : {result['confidence_score']:.2f}\n")
