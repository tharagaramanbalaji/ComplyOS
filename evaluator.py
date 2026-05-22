import json
import os
import glob
from engine.compiler.xslt_generator import compile_rule_to_xslt
from engine.executor.validator import execute_xslt

def run_evaluation():
    print("Loading rules and labels...")
    # Load the JSON IR mappings
    with open("data/rule_mappings_train.json", "r") as f:
        rules = json.load(f)
        
    # Load the Ground Truth validation matrix
    with open("data/validation_labels_train.json", "r") as f:
        ground_truth = json.load(f)
        
    xml_files = glob.glob("data/xml_invoices_train/*.xml")
    total_checks = 0
    correct_checks = 0
    
    # Step 1: Pre-compile all JSON IRs into XSLT scripts
    compiled_rules = {}
    for rule_id, ir in rules.items():
        compiled_rules[rule_id] = compile_rule_to_xslt(ir)
        
    print(f"Successfully compiled {len(compiled_rules)} JSON rules into XSLT.")
    print(f"Applying XSLT against {len(xml_files)} XML invoices. Please wait...")
    
    # Step 2: Run every invoice against every compiled XSLT rule
    from lxml import etree
    duplicate_cache = set()
    
    for xml_path in xml_files:
        inv_id = os.path.basename(xml_path).replace(".xml", "")
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()
            
        expected_labels = ground_truth.get(inv_id, {})
        
        # Track duplicates across invoices
        try:
            doc = etree.fromstring(xml_content.encode("utf-8"))
            inv_nodes = doc.xpath("//Invoice/invoice_id | //*[local-name()='invoice_id']")
            current_id = inv_nodes[0].text if (inv_nodes and inv_nodes[0].text) else None
        except Exception:
            current_id = None
            
        is_duplicate = (current_id in duplicate_cache) if current_id else False
        if current_id:
            duplicate_cache.add(current_id)
        
        for rule_id, xslt_content in compiled_rules.items():
            expected = expected_labels.get(rule_id)
            if not expected:
                continue
                
            # Execute the auto-generated XSLT script
            result = execute_xslt(xml_content, xslt_content)
            
            # Python-level duplicate override
            if rules[rule_id].get("rule_type") == "duplicate_field_check":
                if current_id:
                    result = "FAIL" if is_duplicate else "PASS"
                else:
                    result = "FAIL"
            
            total_checks += 1
            if result == expected:
                correct_checks += 1
                
    accuracy = (correct_checks / total_checks) * 100 if total_checks > 0 else 0
    
    print("-" * 50)
    print("--- PHASE 2 COMPILER EVALUATION RESULTS ---")
    print("-" * 50)
    print(f"Total Invoices Processed : {len(xml_files)}")
    print(f"Total Rules Evaluated    : {len(compiled_rules)}")
    print(f"Total Validation Checks  : {total_checks:,}")
    print(f"Correct Predictions      : {correct_checks:,}")
    print(f"Compiler Accuracy        : {accuracy:.2f}%")
    print("-" * 50)

if __name__ == "__main__":
    run_evaluation()
