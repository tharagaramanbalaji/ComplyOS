import json
import random
import glob
import os
from engine.compiler.xslt_generator import compile_rule_to_xslt
from engine.executor.validator import execute_xslt

def start_interactive_demo():
    print("Loading ComplyOS Validation Engine...")

    # Load JSON IRs
    with open("rule_mappings_train.json", "r") as f:
        rules = json.load(f)

    # Load plain English rules to show what the user "typed"
    english_rules = {}
    with open("rules_train.txt", "r") as f:
        for line in f:
            r = json.loads(line)
            english_rules[r["rule_id"]] = r["rule_text"]

    test_invoices = glob.glob("xml_invoices_test/*.xml")

    while True:
        print("\n" + "="*60)
        print("🔍 COMPLYOS INTERACTIVE VALIDATION DEMO 🔍")
        print("="*60)
        
        # Pick a random rule and invoice
        rule_id = random.choice(list(rules.keys()))
        invoice_path = random.choice(test_invoices)
        
        with open(invoice_path, "r") as f:
            xml_content = f.read()
            
        print(f"\n📄 Loaded Invoice: {os.path.basename(invoice_path)}")
        print(f"🗣️  User Rule: \"{english_rules[rule_id]}\"")
        
        input("\n[Press Enter] to parse English into JSON IR...")
        print("-" * 40)
        print(json.dumps(rules[rule_id], indent=2))
        print("-" * 40)
        
        input("\n[Press Enter] to compile JSON IR into XSLT...")
        xslt_code = compile_rule_to_xslt(rules[rule_id])
        print("-" * 40)
        print(xslt_code.strip())
        print("-" * 40)
        
        input("\n[Press Enter] to execute XSLT against the XML Invoice...")
        result = execute_xslt(xml_content, xslt_code)
        
        print("\n" + "*" * 40)
        if result == "PASS":
            print(f"✅ FINAL RESULT: {result} (Invoice Complies with Rule)")
        else:
            print(f"❌ FINAL RESULT: {result} (Invoice Violated Rule)")
        print("*" * 40)
            
        cont = input("\nRun another random test? (y/n): ")
        if cont.lower() != 'y':
            print("\nExiting demo. Goodbye!")
            break

if __name__ == "__main__":
    start_interactive_demo()
