import json
import random
import os

# Seed for reproducibility so the generated data is consistent
random.seed(42)

# Define the base fields to build rules around
fields = ["invoice_id", "issue_date", "seller_name", "buyer_name", "currency_code", 
          "taxable_amount", "tax_amount", "payable_amount", "tax_category", "tax_exemption_reason",
          "line_items", "seller_address", "buyer_address", "payment_terms", "due_date"]

# Synonyms for variation in natural language
must_synonyms = ["must be", "is required to be", "should be", "has to be"]
present_synonyms = ["present", "provided", "included", "specified"]

rules = []
rule_id_counter = 1

def add_rule(r_type, text, severity, err_msg):
    global rule_id_counter
    rules.append({
        "rule_id": f"RULE_{rule_id_counter:03d}",
        "rule_text": text,
        "severity": severity,
        "rule_type": r_type,
        "expected_error_message": err_msg
    })
    rule_id_counter += 1

# 1. required_field
for f in fields:
    for must in must_synonyms[:3]:
        for pres in present_synonyms[:2]:
             add_rule("required_field", f"The {f.replace('_', ' ')} {must} {pres} on the invoice.", "ERROR", f"Missing {f}")

# 2. conditional_required_field
conds = [
    ("tax_category", "Exempt", "tax_exemption_reason"), 
    ("currency_code", "EUR", "tax_amount"),
    ("seller_country", "US", "buyer_address"),
    ("payment_method", "Bank Transfer", "bank_account_number"),
    ("taxable_amount", "0", "tax_exemption_reason")
]
for cond_f, cond_v, target_f in conds:
    for must in must_synonyms:
        add_rule("conditional_required_field", 
                 f"If {cond_f.replace('_', ' ')} equals '{cond_v}', then {target_f.replace('_', ' ')} {must} present.", 
                 "ERROR", f"{target_f} missing for condition {cond_f}={cond_v}")

# 3. date_validation
date_fields = ["issue_date", "due_date"]
for df in date_fields:
    for must in must_synonyms:
        add_rule("date_validation", f"The {df.replace('_', ' ')} {must} a valid date in the past or present.", "ERROR", f"Invalid {df}")
        add_rule("date_validation", f"Ensure the {df.replace('_', ' ')} is not a future date.", "ERROR", f"Future {df} not allowed")

# 4. numeric_comparison
num_fields = ["taxable_amount", "tax_amount", "payable_amount", "line_item_amount"]
for nf in num_fields:
    for must in must_synonyms:
        add_rule("numeric_comparison", f"The {nf.replace('_', ' ')} {must} greater than or equal to zero.", "ERROR", f"Negative {nf}")
        add_rule("numeric_comparison", f"Value of {nf.replace('_', ' ')} {must} be a valid non-negative number.", "ERROR", f"Invalid {nf}")

# 5. amount_calculation
calc_phrases = [
    "must equal the sum of taxable amount and tax amount",
    "should exactly match taxable amount plus tax amount",
    "has to be calculated as taxable amount + tax amount",
    "is required to equal taxable amount added to tax amount"
]
for phrase in calc_phrases:
    add_rule("amount_calculation", f"The payable amount {phrase}.", "ERROR", "Payable amount calculation mismatch")
    add_rule("amount_calculation", f"Line item totals {must_synonyms[0]} equal the taxable amount.", "ERROR", "Line items do not match taxable amount")

# 6. currency_consistency
for phrase in ["match", "be consistent with", "equal"]:
    add_rule("currency_consistency", f"The line item currency must {phrase} the invoice currency code.", "ERROR", "Inconsistent currency codes")
    add_rule("currency_consistency", f"Invoice currency code should {phrase} the payment currency.", "ERROR", "Currency mismatch")

# 7. tax_category_validation
for must in must_synonyms:
    add_rule("tax_category_validation", f"The tax category {must} a recognized standard code (e.g., S, E, Z).", "ERROR", "Invalid tax category code")
    add_rule("tax_category_validation", f"Tax category on line items {must} valid.", "ERROR", "Line item tax category invalid")

# 8. duplicate_field_check
for f in ["invoice_id", "document_identifier", "transaction_id"]:
    for must in must_synonyms:
        add_rule("duplicate_field_check", f"The {f.replace('_', ' ')} {must} unique and not seen in previous invoices.", "ERROR", f"Duplicate {f}")

# Shuffle the large list of generated rules to ensure varied distribution
random.shuffle(rules)

# Extract exactly 130 rules to meet requirements (100 train, 30 test)
final_rules = rules[:130]

train_rules = final_rules[:100]
test_rules = final_rules[100:]

print("Saving to files...")

# Write to rules_train.txt as JSONL (JSON Lines)
with open('rules_train.txt', 'w') as f:
    for r in train_rules:
        f.write(json.dumps(r) + '\n')

# Write to rules_test.txt as JSONL
with open('rules_test.txt', 'w') as f:
    for r in test_rules:
        f.write(json.dumps(r) + '\n')

print(f"Generated {len(train_rules)} rules in rules_train.txt")
print(f"Generated {len(test_rules)} rules in rules_test.txt")
