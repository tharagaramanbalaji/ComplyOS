import os
import json
import random
from typing import List, Dict
import datetime

class DatasetGenerator:
    def __init__(self, base_dir="datasets_output"):
        self.base_dir = base_dir
        self.rules_train = os.path.join(base_dir, "rules_train.txt")
        self.rules_test = os.path.join(base_dir, "rules_test.txt")
        self.xml_train_dir = os.path.join(base_dir, "xml_invoices_train")
        self.xml_test_dir = os.path.join(base_dir, "xml_invoices_test")
        self.labels_train = os.path.join(base_dir, "validation_labels_train.json")
        self.mappings_train = os.path.join(base_dir, "rule_mappings_train.json")
        
        self.setup_directories()

    def setup_directories(self):
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.xml_train_dir, exist_ok=True)
        os.makedirs(self.xml_test_dir, exist_ok=True)

    def generate_rules(self) -> List[Dict]:
        rules = [
            ("If tax amount > 0 tax category required", "conditional_required_field", "Missing tax category when tax amount > 0", "ERROR"),
            ("issue date is required", "required_field", "Invoice must have an issue date", "FATAL"),
            ("currency code is required", "required_field", "Currency code is missing", "ERROR"),
            ("payable amount must be greater than 0", "numeric_comparison", "Payable amount must be positive", "ERROR"),
            ("taxable amount is required", "required_field", "Taxable amount is mandatory", "ERROR"),
            ("buyer name is required", "required_field", "Buyer name cannot be empty", "ERROR"),
            ("issue date cannot be in the future", "date_validation", "Issue date cannot be in the future", "ERROR"),
            ("invoice identifier must be unique", "duplicate_field_check", "Invoice ID already exists", "ERROR"),
            ("currency must be consistent", "currency_consistency", "Currency mismatch detected", "ERROR"),
            ("tax category must be valid", "tax_category_validation", "Invalid tax category", "ERROR"),
            ("payable amount must equal taxable amount + tax amount", "amount_calculation", "Amount mismatch", "ERROR")
        ]
        
        generated_rules = []
        for i in range(250):
            base = random.choice(rules)
            ir = {"type": base[1]}
            if base[1] == "required_field": ir["field"] = base[0].replace(' is required', '').replace(' ', '_')
            elif base[1] == "numeric_comparison": ir.update({"field": "payable_amount", "operator": ">", "value": "0"})
            elif base[1] == "conditional_required_field": ir.update({"condition": "tax_amount>0", "required_field": "tax_category"})
            elif base[1] == "amount_calculation": ir.update({"target_field": "payable_amount", "operator": "==", "field_1": "taxable_amount", "field_2": "tax_amount"})
            elif base[1] in ["date_validation", "duplicate_field_check", "tax_category_validation"]:
                f_map = {"date_validation": "issue_date", "duplicate_field_check": "invoice_id", "tax_category_validation": "tax_category"}
                ir["field"] = f_map[base[1]]
                if base[1] == "date_validation": ir.update({"operator": "<=", "value": "TODAY"})

            rule_obj = {
                "rule_id": f"R-{i+1000}",
                "rule_text": base[0],
                "rule_type": base[1],
                "expected_error_message": base[2],
                "severity": base[3],
                "structured_IR": ir,
                "parsed_entities": {},
                "validation_logic": f"Execute {base[1]} on {ir.get('field', 'invoice')}",
                "xslt_mapping": f"<xsl:choose><xsl:when test='...'><Error>{base[2]}</Error></xsl:when></xsl:choose>"
            }
            generated_rules.append(rule_obj)

        with open(self.rules_train, 'w') as f:
            for r in generated_rules[:200]:
                f.write(f"{r['rule_id']}|{r['rule_text']}|{r['severity']}|{r['rule_type']}|{r['expected_error_message']}\n")

        with open(self.rules_test, 'w') as f:
            for r in generated_rules[200:]:
                f.write(f"{r['rule_id']}|{r['rule_text']}|{r['severity']}|{r['rule_type']}|{r['expected_error_message']}\n")

        with open(self.mappings_train, 'w') as f:
            json.dump(generated_rules[:200], f, indent=4)
            
        return generated_rules

    def generate_xml_invoice(self, invoice_id: str, scenario: str) -> tuple[str, bool, list]:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        future = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        
        issue_date = today
        currency = "USD"
        
        # Ranges compliant with PS
        taxable_amount_val = round(random.uniform(50.0, 250000.0), 2)
        tax_percent = random.uniform(0.0, 0.28)
        tax_amount_val = round(taxable_amount_val * tax_percent, 2)
        payable_val = round(taxable_amount_val + tax_amount_val, 2)
        
        taxable_amount = f"{taxable_amount_val:.2f}"
        tax_amount = f"{tax_amount_val:.2f}"
        payable = f"{payable_val:.2f}"
        
        tax_cat = "S"
        buyer = "Acme Corp"
        
        # Line Items
        num_items = random.randint(1, 50)
        line_items_xml = ""
        for i in range(num_items):
            line_items_xml += f'''
    <cac:InvoiceLine>
        <cbc:ID>{i+1}</cbc:ID>
        <cbc:InvoicedQuantity>1</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount>{round(taxable_amount_val/num_items, 2):.2f}</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>Product {i+1}</cbc:Name>
            <cac:ClassifiedTaxCategory>
                <cbc:ID>{tax_cat}</cbc:ID>
                <cbc:Percent>{round(tax_percent*100, 2)}</cbc:Percent>
            </cac:ClassifiedTaxCategory>
        </cac:Item>
    </cac:InvoiceLine>'''
        
        is_valid = True
        errors = []
        
        if scenario == "missing_fields":
            buyer = ""
            is_valid, errors = False, [{"rule_id": "SYS", "message": "Buyer name cannot be empty", "severity": "ERROR"}]
        elif scenario == "future_date":
            issue_date = future
            is_valid, errors = False, [{"rule_id": "SYS", "message": "Issue date cannot be in the future", "severity": "ERROR"}]
        elif scenario == "currency_mismatch":
            currency = ""
            is_valid, errors = False, [{"rule_id": "SYS", "message": "Currency code is missing", "severity": "ERROR"}]
        elif scenario == "tax_mismatch":
            tax_cat = "INVALID"
            is_valid, errors = False, [{"rule_id": "SYS", "message": "Invalid tax category", "severity": "ERROR"}]
        elif scenario == "payable_mismatch":
            payable = "900.00"
            is_valid, errors = False, [{"rule_id": "SYS", "message": "Amount mismatch", "severity": "ERROR"}]
        elif scenario == "malformed":
            return "<Invoice><cbc:ID>Malformed</Invoice>", False, [{"rule_id": "SYS", "message": "Malformed XML", "severity": "FATAL"}]
            
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ID>{invoice_id}</cbc:ID>
    <cbc:IssueDate>{issue_date}</cbc:IssueDate>
    <cbc:DocumentCurrencyCode>{currency}</cbc:DocumentCurrencyCode>
    <cac:AccountingCustomerParty>
        <cac:Party><cac:PartyName><cbc:Name>{buyer}</cbc:Name></cac:PartyName></cac:Party>
    </cac:AccountingCustomerParty>
    <cac:TaxTotal>
        <cbc:TaxAmount>{tax_amount}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount>{taxable_amount}</cbc:TaxableAmount>
            <cac:TaxCategory>
                <cbc:ID>{tax_cat}</cbc:ID>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:PayableAmount>{payable}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    {line_items_xml}
</Invoice>'''
        return xml, is_valid, errors

    def generate_invoices(self, rules: List[Dict]):
        labels = []
        scenarios = ["valid", "valid", "missing_fields", "future_date", "currency_mismatch", "tax_mismatch", "payable_mismatch", "malformed"]
        
        for i in range(500):
            scenario = random.choice(scenarios)
            inv_id = f"INV-{i+1000}"
            # simulate duplicate id check occasionally
            if i % 50 == 0:
                inv_id = "INV-DUPLICATE"
                if scenario == "valid": 
                    scenario = "duplicate"
            
            if scenario == "duplicate":
                xml_content, is_valid, errors = self.generate_xml_invoice(inv_id, "valid")
                is_valid = False
                errors = [{"rule_id": "SYS", "message": "Invoice ID already exists", "severity": "ERROR"}]
            else:
                xml_content, is_valid, errors = self.generate_xml_invoice(inv_id, scenario)
            
            target_dir = self.xml_train_dir if i < 400 else self.xml_test_dir
            with open(os.path.join(target_dir, f"{inv_id}_{i}.xml"), 'w') as f:
                f.write(xml_content)
                
            if i < 400:
                labels.append({
                    "invoice_id": inv_id,
                    "rules_applied": [r["rule_id"] for r in rules[:5]],
                    "pass_fail": "PASS" if is_valid else "FAIL",
                    "validation_errors": errors,
                    "trace": [{"rule_id": "SYS", "passed": is_valid, "evaluation_details": "Generated log"}],
                    "severity": "PASS" if is_valid else errors[0]["severity"]
                })
            
        with open(self.labels_train, 'w') as f:
            json.dump(labels, f, indent=4)

if __name__ == "__main__":
    gen = DatasetGenerator()
    rules = gen.generate_rules()
    gen.generate_invoices(rules)
    print("Datasets generated successfully.")
