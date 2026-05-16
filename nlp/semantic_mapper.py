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
