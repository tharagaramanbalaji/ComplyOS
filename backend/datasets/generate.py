import random
import os
import json
import xml.etree.ElementTree as ET

def generate_dataset():
    out_dir = "../datasets_output"
    os.makedirs(f"{out_dir}/xml_invoices_train", exist_ok=True)
    os.makedirs(f"{out_dir}/xml_invoices_test", exist_ok=True)

    rules = [
        "Tax amount should be greater than 0",
        "If tax amount > 100 tax category required",
        "Invoice ID required",
        "Issue date cannot be future",
        "Invoice ID unique",
        "Tax category should be S",
        "Whenever payable amount exceeds 10000 buyer VAT should exist",
        "Any invoice with tax amount greater than zero requires tax category"
    ]
    
    # Expand rules
    all_rules = []
    for _ in range(150):
        all_rules.append(random.choice(rules))
        
    with open(f"{out_dir}/rules_train.txt", "w") as f:
        f.write("\n".join(all_rules[:100]))
    with open(f"{out_dir}/rules_test.txt", "w") as f:
        f.write("\n".join(all_rules[100:]))
        
    rule_mappings = [{"rule_id": f"R{i}", "text": r} for i, r in enumerate(all_rules)]
    with open(f"{out_dir}/rule_mappings_train.json", "w") as f:
        json.dump(rule_mappings, f, indent=2)

    labels = []
    
    def generate_xml(idx, is_valid, is_test=False):
        taxable = round(random.uniform(50, 250000), 2)
        tax_rate = random.choice([0, 5, 12, 18, 28])
        tax = round(taxable * (tax_rate / 100), 2)
        payable = round(taxable + tax, 2)
        
        issue_date = "2026-05-18"
        if not is_valid and random.random() < 0.2:
            issue_date = "2099-01-01" # future date
            
        if not is_valid and random.random() < 0.2:
            tax = 0 # invalidate tax > 0 rule
            
        if not is_valid and random.random() < 0.2:
            payable = taxable + tax + 10 # invalidate calculation
            
        cat = "S" if tax > 0 else "O"
        if not is_valid and random.random() < 0.2:
            cat = "" # empty category
            
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
    <cbc:ID>INV-{idx}</cbc:ID>
    <cbc:IssueDate>{issue_date}</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>USD</cbc:DocumentCurrencyCode>
    <cac:AccountingSupplierParty>
        <cac:Party><cac:PartyName><cbc:Name>Seller Inc</cbc:Name></cac:PartyName></cac:Party>
    </cac:AccountingSupplierParty>
    <cac:AccountingCustomerParty>
        <cac:Party><cac:PartyName><cbc:Name>Buyer Corp</cbc:Name></cac:PartyName>
        <cac:PartyTaxScheme><cbc:CompanyID>{"VAT123" if payable > 10000 or is_valid else ""}</cbc:CompanyID></cac:PartyTaxScheme>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cbc:TaxAmount>{tax}</cbc:TaxAmount>
    <cbc:TaxableAmount>{taxable}</cbc:TaxableAmount>
    <cbc:PayableAmount>{payable}</cbc:PayableAmount>
    <cac:TaxCategory><cbc:ID>{cat}</cbc:ID></cac:TaxCategory>
'''
        for i in range(random.randint(1, 5)):
            xml += f'''    <cac:InvoiceLine>
        <cbc:ID>{i}</cbc:ID>
        <cbc:LineExtensionAmount>{round(taxable/5, 2)}</cbc:LineExtensionAmount>
    </cac:InvoiceLine>
'''
        xml += "</Invoice>"
        
        folder = "xml_invoices_test" if is_test else "xml_invoices_train"
        with open(f"{out_dir}/{folder}/inv_{idx}.xml", "w") as f:
            f.write(xml)
            
        return {"invoice_id": f"inv_{idx}.xml", "valid": is_valid}

    for i in range(500):
        is_valid = random.random() > 0.4 # 40% invalid
        labels.append(generate_xml(i, is_valid, is_test=(i>400)))
        
    with open(f"{out_dir}/validation_labels_train.json", "w") as f:
        json.dump(labels, f, indent=2)

if __name__ == "__main__":
    generate_dataset()
