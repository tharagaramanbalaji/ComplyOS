import json
import re

mappings = {}

print("Reading rules_train.txt...")

with open('rules_train.txt', 'r') as f:
    for line in f:
        rule = json.loads(line.strip())
        rule_id = rule['rule_id']
        r_type = rule['rule_type']
        err_msg = rule['expected_error_message']
        
        # Base Intermediate Representation (IR) structure
        ir = {"rule_type": r_type}
        
        # Parse the error message we generated previously to reconstruct the exact fields
        if r_type == "required_field":
            field = err_msg.replace("Missing ", "")
            ir["field"] = field
            ir["check"] = "is_present"
            
        elif r_type == "conditional_required_field":
            # Format: "{target_f} missing for condition {cond_f}={cond_v}"
            match = re.match(r"(.+) missing for condition (.+)=(.+)", err_msg)
            if match:
                target_f, cond_f, cond_v = match.groups()
                ir["condition"] = {
                    "field": cond_f, 
                    "operator": "==", 
                    "value": cond_v
                }
                ir["action"] = {
                    "field": target_f, 
                    "check": "is_present"
                }
                
        elif r_type == "date_validation":
            if "Future" in err_msg:
                field = err_msg.replace("Future ", "").replace(" not allowed", "")
            else:
                field = err_msg.replace("Invalid ", "")
                
            ir["field"] = field
            ir["operator"] = "<="
            ir["value"] = "CURRENT_DATE"
                
        elif r_type == "numeric_comparison":
            field = err_msg.replace("Negative ", "").replace("Invalid ", "")
            ir["field"] = field
            ir["operator"] = ">="
            ir["value"] = 0
            
        elif r_type == "amount_calculation":
            if "Payable amount" in err_msg:
                ir["field"] = "payable_amount"
                ir["equation"] = "taxable_amount + tax_amount"
            else:
                ir["field"] = "line_items[*].amount"
                ir["aggregation"] = "sum"
                ir["expected_match"] = "taxable_amount"
                
        elif r_type == "currency_consistency":
            if "Inconsistent" in err_msg:
                ir["field"] = "line_items[*].currency_code"
                ir["expected_match"] = "currency_code"
            else:
                ir["field"] = "currency_code"
                ir["expected_match"] = "payment_currency"
                
        elif r_type == "tax_category_validation":
            if "Line item" in err_msg:
                ir["field"] = "line_items[*].tax_category"
            else:
                ir["field"] = "tax_category"
            ir["valid_values"] = ["S", "E", "Z", "AE", "K", "G", "O"] # Standard tax category codes
                
        elif r_type == "duplicate_field_check":
            field = err_msg.replace("Duplicate ", "")
            ir["field"] = field
            ir["check"] = "is_unique_globally"
            
        mappings[rule_id] = ir

# Write to the JSON mappings file
with open('rule_mappings_train.json', 'w') as f:
    json.dump(mappings, f, indent=2)

print(f"Generated rule_mappings_train.json successfully mapped exactly {len(mappings)} rules!")
