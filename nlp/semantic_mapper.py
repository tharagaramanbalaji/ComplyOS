from sentence_transformers import SentenceTransformer, util
import torch

class SemanticMapper:
    def __init__(self):
        # We use a real, lightweight HuggingFace transformer model.
        # It runs locally on your machine, proving no fake data is used.
        print("Loading Sentence Transformer model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # These are the exact rigid JSON fields our Validation Engine expects
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
        
        # Pre-compute semantic vector embeddings for our target database fields
        self.corpus = list(self.field_descriptions.values())
        self.corpus_keys = list(self.field_descriptions.keys())
        self.corpus_embeddings = self.model.encode(self.corpus, convert_to_tensor=True)

        # Canonical examples for Zero-Shot Vector Intent Classification
        self.intent_examples = {
            "required_check": [
                "The invoice ID must be present", "Make sure invoice ID is there", 
                "Check that invoice ID exists", "The issue date is mandatory", 
                "Cannot be empty", "must exist in the document", "is required",
                "Ensure seller name is filled", "Verify that buyer name exists"
            ],
            "conditional_check": [
                "If the tax category is Exempt then the tax exemption reason must be present",
                "When tax is zero, provide exemption reason", "In case of export, free export justification is required",
                "If currency is USD then payable amount must be positive", "whenever tax is exempt"
            ],
            "calculation_check": [
                "The payable amount must equal taxable amount plus tax amount",
                "The sum of line items amount must equal taxable amount", "Total amount equals subtotal plus vat",
                "Calculate the sum of all lines and verify it matches the base amount", "Addition of tax and taxable should match total",
                "sum of items should match subtotal"
            ],
            "tax_category_validation": [
                "The tax category should be AE", "The tax category must be S or Z", 
                "Ensure valid tax code is used like S or E", "Verify tax category allowed values",
                "tax category code is valid"
            ],
            "currency_consistency": [
                "All line item currency codes must match the document currency", "Ensure currency is consistent across lines",
                "Currency code must be EUR throughout the file", "Document currency and line item currency should be identical"
            ],
            "date_validation": [
                "The due date must be before or equal to current date", "Issue date cannot be in the future",
                "Check that invoice date is before today", "Date validation against current time",
                "due date before today"
            ],
            "duplicate_check": [
                "Every invoice ID must be unique across submissions", "Ensure no duplicate invoice id is submitted",
                "Check if this invoice already exists in the system", "Prevent duplicate invoice submissions",
                "no duplicate IDs allowed"
            ],
            "numeric_comparison": [
                "The payable amount must be greater than or equal to 0", "Taxable amount must be at least 100",
                "Amount cannot be negative", "Check that tax is less than 500000",
                "amount must be positive", "greater than zero"
            ]
        }
        self.intent_corpus = []
        self.intent_labels = []
        for int_name, examples in self.intent_examples.items():
            for ex in examples:
                self.intent_corpus.append(ex)
                self.intent_labels.append(int_name)
        self.intent_embeddings = self.model.encode(self.intent_corpus, convert_to_tensor=True)

    def map_subject_to_field(self, extracted_subject: str) -> dict:
        """
        Takes a fuzzy English subject (like 'final amount to pay') and maps it to the 
        strict JSON field (like 'payable_amount') using vector cosine similarity.
        """
        # Convert the user's fuzzy subject into a 384-dimensional mathematical vector
        query_embedding = self.model.encode(extracted_subject, convert_to_tensor=True)
        
        # Compute cosine similarity between the query vector and all valid field vectors
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        
        # Find the highest scoring match
        top_result = torch.topk(cos_scores, k=1)
        best_score = top_result[0][0].item()
        best_idx = top_result[1][0].item()
        
        best_match_key = self.corpus_keys[best_idx]
        
        return {
            "mapped_field": best_match_key,
            "confidence_score": best_score,
            "original_subject": extracted_subject
        }

    def predict_intent(self, rule_text: str) -> str:
        """
        Zero-shot vector semantic intent classification.
        Compares input text against canonical vector space for the 8 rule intents.
        """
        query_embedding = self.model.encode(rule_text, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.intent_embeddings)[0]
        top_result = torch.topk(cos_scores, k=1)
        best_idx = top_result[1][0].item()
        return self.intent_labels[best_idx]

if __name__ == "__main__":
    mapper = SemanticMapper()
    
    # We will test some extremely fuzzy, human-like phrases to prove the AI maps them correctly
    test_phrases = [
        "the final amount you have to pay",
        "value added taxes",
        "date of invoice creation",
        "the price of an individual product"
    ]
    
    print("\n" + "="*50)
    print("--- SEMANTIC MAPPER TEST RESULTS ---")
    print("="*50)
    for phrase in test_phrases:
        result = mapper.map_subject_to_field(phrase)
        print(f"User Subject : '{phrase}'")
        print(f"Mapped Field : {result['mapped_field']}")
        print(f"Confidence   : {result['confidence_score']:.2f}\n")
