import json
import glob
import random
import os
from nlp.parser import NLPRuleParser
from engine.compiler.xslt_generator import compile_rule_to_xslt
from engine.executor.validator import execute_xslt

def live_demo():
    print("Initializing Live ComplyOS Engine (Loading NLP models)...")
    parser = NLPRuleParser()
    test_invoices = glob.glob("xml_invoices_test/*.xml")
    
    print("\n" + "="*60)
    print("⚡ COMPLYOS LIVE END-TO-END ENGINE ⚡")
    print("="*60)
    print("The problem statement requires these 8 rule types:")
    print("  1. required_field")
    print("  2. conditional_required_field")
    print("  3. date_validation")
    print("  4. numeric_comparison")
    print("  5. amount_calculation")
    print("  6. currency_consistency")
    print("  7. tax_category_validation")
    print("  8. duplicate_field_check")
    print("-" * 60)
    
    while True:
        rule_text = input("\n📝 Enter your compliance rule in plain English (or type 'exit' to quit):\n> ")
        if rule_text.lower() == 'exit':
            break
            
        print("\n[1] NLP PARSING (English -> JSON IR)...")
        try:
            json_ir = parser.parse_rule(rule_text)
            print("-" * 40)
            print(json.dumps(json_ir, indent=2))
            print("-" * 40)
        except Exception as e:
            print(f"Error parsing rule: {e}")
            continue
            
        input("\n[Press Enter to Compile to XSLT...]")
        print("\n[2] COMPILING (JSON IR -> XSLT)...")
        try:
            xslt_code = compile_rule_to_xslt(json_ir)
            print("-" * 40)
            print(xslt_code.strip())
            print("-" * 40)
        except Exception as e:
            print(f"Error compiling XSLT: {e}")
            continue
            
        input("\n[Press Enter to run against an XML Invoice...]")
        print("\n[3] EXECUTING VALIDATION...")
        invoice_path = random.choice(test_invoices)
        print(f"Loaded XML Invoice: {os.path.basename(invoice_path)}")
        with open(invoice_path, "r") as f:
            xml_content = f.read()
            
        result = execute_xslt(xml_content, xslt_code)
        
        print("\n" + "*" * 40)
        if result == "PASS":
            print(f"✅ FINAL RESULT: {result} (Invoice Complies with Rule)")
        else:
            print(f"❌ FINAL RESULT: {result} (Invoice Violated Rule)")
        print("*" * 40)

if __name__ == "__main__":
    live_demo()
