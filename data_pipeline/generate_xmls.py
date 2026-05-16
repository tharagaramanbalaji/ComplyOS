import os
import json
import random
import uuid
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Seed for reproducibility
random.seed(42)

TRAIN_COUNT = 500
TEST_COUNT = 150
INVALID_RATE = 0.4  # 40% invalid rate to ensure engine catches errors

# Load the deterministic rules we mapped
with open("rule_mappings_train.json", "r") as f:
    rule_mappings = json.load(f)

# Create output directories
os.makedirs("xml_invoices_train", exist_ok=True)
os.makedirs("xml_invoices_test", exist_ok=True)

# Fake data pools
sellers = ["Acme Corp", "Globex", "Initech", "Soylent Corp", "Stark Industries", "Wayne Enterprises"]
buyers = ["Umbrella Corp", "Cyberdyne", "Hooli", "Massive Dynamic", "Stark Industries"]
currencies = ["USD", "EUR", "GBP", "JPY", "CAD"]
tax_categories = ["S", "E", "Z", "AE", "K"]

validation_labels = {}
used_invoice_ids = set()

def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    # Remove extra blank lines from pretty print
    return '\n'.join([line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip()])

def generate_invoice_data(is_valid=True):
    invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    
    # Deliberately cause duplicate invoice errors
    if not is_valid and random.random() < 0.1 and used_invoice_ids:
        invoice_id = list(used_invoice_ids)[0]
    used_invoice_ids.add(invoice_id)
    
    # Issue Date logic
    if not is_valid and random.random() < 0.2:
        # Future date error
        issue_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
    else:
        # Valid past date
        issue_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
        
    currency_code = random.choice(currencies)
    
    # Financial amounts
    taxable_amount = round(random.uniform(50, 250000), 2)
    tax_rate = random.uniform(0, 0.28)
    tax_amount = round(taxable_amount * tax_rate, 2)
    payable_amount = round(taxable_amount + tax_amount, 2)
    
    # Deliberately break calculation or put negative numbers
    if not is_valid and random.random() < 0.3:
        if random.random() < 0.5:
            payable_amount = round(payable_amount + random.uniform(10, 100), 2) # Bad math
        else:
            taxable_amount = -abs(taxable_amount) # Negative value error
            
    tax_category = random.choice(tax_categories)
    tax_exemption_reason = "Exempt for export" if tax_category == "E" else ""
    
    if not is_valid and random.random() < 0.2:
        tax_category = "INVALID_TAX_XYZ"
        
    # Generate line items (1 to 50)
    num_lines = random.randint(1, 50)
    line_items = []
    remaining_amount = taxable_amount
    for i in range(num_lines):
        if i == num_lines - 1:
            item_amount = round(remaining_amount, 2)
        else:
            item_amount = round(remaining_amount / (num_lines - i) * random.uniform(0.5, 1.5), 2)
        remaining_amount -= item_amount
        
        item_currency = currency_code
        if not is_valid and random.random() < 0.1:
            item_currency = "BAD_CURRENCY" # Inconsistent currency error
            
        line_items.append({
            "line_id": str(i+1),
            "description": f"Product Item {i+1}",
            "amount": item_amount,
            "currency_code": item_currency,
            "tax_category": tax_category
        })
        
    data = {
        "invoice_id": invoice_id,
        "issue_date": issue_date,
        "seller_name": random.choice(sellers),
        "buyer_name": random.choice(buyers),
        "currency_code": currency_code,
        "taxable_amount": taxable_amount,
        "tax_amount": tax_amount,
        "payable_amount": payable_amount,
        "tax_category": tax_category,
        "tax_exemption_reason": tax_exemption_reason,
        "payment_currency": currency_code,
        "seller_address": "123 Business Rd, NY",
        "buyer_address": "456 Enterprise Blvd, CA",
        "payment_terms": "Net 30",
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "line_items": line_items
    }
    
    # Deliberately drop required fields
    if not is_valid and random.random() < 0.4:
        drop_candidates = ["tax_amount", "seller_name", "buyer_name", "payable_amount", "issue_date", "seller_address"]
        fields_to_drop = random.sample(drop_candidates, random.randint(1, 3))
        for f in fields_to_drop:
            data[f] = None
            
    return data

def build_xml(data):
    invoice = ET.Element("Invoice")
    
    for key, value in data.items():
        if value is None or key == "line_items":
            continue
        child = ET.SubElement(invoice, key)
        child.text = str(value)
        
    line_items_el = ET.SubElement(invoice, "line_items")
    for item in data.get("line_items", []):
        line = ET.SubElement(line_items_el, "line_item")
        for k, v in item.items():
            child = ET.SubElement(line, k)
            child.text = str(v)
            
    return invoice

def evaluate_rule(data, ir, is_dup):
    """
    Deterministically evaluates an invoice dictionary against our Intermediate Representation logic
    """
    r_type = ir.get("rule_type")
    
    def get_field_val(f_path):
        if f_path == "line_items[*].amount":
            return [i.get("amount") for i in data.get("line_items", [])]
        if f_path == "line_items[*].currency_code":
            return [i.get("currency_code") for i in data.get("line_items", [])]
        if f_path == "line_items[*].tax_category":
            return [i.get("tax_category") for i in data.get("line_items", [])]
        return data.get(f_path)
        
    if r_type == "required_field":
        return get_field_val(ir["field"]) is not None
        
    elif r_type == "conditional_required_field":
        cond = ir["condition"]
        act = ir["action"]
        val = get_field_val(cond["field"])
        if cond["operator"] == "==" and str(val) == cond["value"]:
            return get_field_val(act["field"]) is not None
        return True 
        
    elif r_type == "date_validation":
        val = get_field_val(ir["field"])
        if not val: return True
        try:
            dt = datetime.strptime(val, "%Y-%m-%d")
            today = datetime.now()
            if ir["operator"] == "<=" and ir["value"] == "CURRENT_DATE":
                return dt <= today
        except:
            return False
            
    elif r_type == "numeric_comparison":
        val = get_field_val(ir["field"])
        if val is None: return True
        try:
            val = float(val)
            if ir["operator"] == ">=": return val >= ir["value"]
        except: return False
            
    elif r_type == "amount_calculation":
        if ir["field"] == "payable_amount":
            pay, taxable, tax = get_field_val("payable_amount"), get_field_val("taxable_amount"), get_field_val("tax_amount")
            if pay is None or taxable is None or tax is None: return True
            return round(float(pay), 2) == round(float(taxable) + float(tax), 2)
        elif ir.get("aggregation") == "sum":
            lines = get_field_val(ir["field"])
            match_val = get_field_val(ir["expected_match"])
            if not lines or match_val is None: return True
            try: return round(sum(float(l) for l in lines), 2) == round(float(match_val), 2)
            except: return False
            
    elif r_type == "currency_consistency":
        val = get_field_val(ir["field"])
        match_val = get_field_val(ir["expected_match"])
        if not val or not match_val: return True
        if isinstance(val, list): return all(v == match_val for v in val)
        return val == match_val
        
    elif r_type == "tax_category_validation":
        val = get_field_val(ir["field"])
        valid = ir["valid_values"]
        if not val: return True
        if isinstance(val, list): return all(v in valid for v in val)
        return val in valid
        
    elif r_type == "duplicate_field_check":
        if ir["field"] == "invoice_id":
            return not is_dup
            
    return True

print(f"Generating {TRAIN_COUNT} Train XMLs and {TEST_COUNT} Test XMLs...")

# Generate training data and eval labels
global_seen_invoices = set()
for i in range(TRAIN_COUNT):
    is_valid = random.random() > INVALID_RATE
    data = generate_invoice_data(is_valid)
    
    inv_id = data["invoice_id"]
    is_dup = inv_id in global_seen_invoices
    global_seen_invoices.add(inv_id)
    
    # Save XML
    xml_filename = f"xml_invoices_train/{inv_id}.xml"
    with open(xml_filename, "w") as f:
        f.write(prettify(build_xml(data)))
        
    # Evaluate against rules
    labels = {}
    for rule_id, ir in rule_mappings.items():
        passed = evaluate_rule(data, ir, is_dup)
        labels[rule_id] = "PASS" if passed else "FAIL"
            
    validation_labels[inv_id] = labels

# Save labels
print("Saving validation_labels_train.json...")
with open("validation_labels_train.json", "w") as f:
    json.dump(validation_labels, f, indent=2)

# Generate test data
for i in range(TEST_COUNT):
    is_valid = random.random() > INVALID_RATE
    data = generate_invoice_data(is_valid)
    inv_id = data["invoice_id"]
    xml_filename = f"xml_invoices_test/{inv_id}.xml"
    with open(xml_filename, "w") as f:
        f.write(prettify(build_xml(data)))

print("✅ Dataset generation perfectly completed!")
