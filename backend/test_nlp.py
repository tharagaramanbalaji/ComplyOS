"""
Comprehensive NLP parser + XSLT validation test suite.
Run from d:/ComplyOS/backend via:
    .\\venv\\Scripts\\python test_nlp.py
"""
import os, sys
# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import json
from parser.rule_parser import RuleParser
from engine.xslt_generator import XSLTGenerator

# ── test cases ────────────────────────────────────────────────────────────────
TEST_CASES = [
    ("Tax amount >0",                                  "numeric_comparison",        "tax_amount",  ">",  0),
    ("Tax amount should be greater than 0",            "numeric_comparison",        "tax_amount",  ">",  0),
    ("Tax amount should exceed zero",                  "numeric_comparison",        "tax_amount",  ">",  0),
    ("Invoice date should not exceed current date",    "date_validation",           "issue_date",  "<=", "current_date"),
    ("Invoice ID required",                            "required_field",            "invoice_id",  None, None),
    ("Invoice ID unique",                              "duplicate_field_check",     "invoice_id",  None, None),
    ("If tax amount >100 tax category required",       "conditional_required_field","tax_amount",  ">",  100),
    ("Invocie ID required",                            "required_field",            "invoice_id",  None, None),
    ("Tax amunt >0",                                   "numeric_comparison",        "tax_amount",  ">",  0),
    ("Tax category should be AE",                      "tax_category_validation",   "tax_category",None, None),
    ("Tax amount high",                                "unknown",                   None,          None, None),
]

SEP = "-" * 60


def check(label, got, expected):
    ok = (got == expected) if expected is not None else True
    mark = "PASS" if ok else "FAIL"
    return ok, f"    [{mark}] {label}: got={got!r}  expected={expected!r}"


def run():
    parser = RuleParser()
    gen    = XSLTGenerator()
    passed = 0
    total  = len(TEST_CASES)
    failures = []

    print("\n" + "=" * 60)
    print("  ComplyOS Parser Validation Report")
    print("=" * 60 + "\n")

    for idx, (rule_text, exp_type, exp_field, exp_op, exp_val) in enumerate(TEST_CASES, 1):
        print(f"[{idx}/{total}]  Input: {rule_text!r}")
        try:
            rules = parser.parse(rule_text)
            r = rules[0]
            ir = r.structured_IR
            debug = r.parsed_entities

            print(f"  Normalized : {debug.get('normalized')!r}")
            print(f"  Mapped     : {debug.get('after_synonym_map')!r}")
            print(f"  Intent     : {debug.get('intent')!r}")
            print(f"  Confidence : {debug.get('confidence'):.2f}")
            print(f"  IR type    : {ir.type!r}")
            print(f"  IR payload : {ir.model_dump(exclude_none=True)}")

            all_ok = True
            type_ok, type_msg = check("rule_type", ir.type, exp_type)
            all_ok = all_ok and type_ok
            print(type_msg)

            if exp_field is not None:
                actual_field = ir.field
                if ir.type == "conditional_required_field" and isinstance(ir.condition, dict):
                    actual_field = ir.condition.get("field")
                elif ir.type == "tax_category_validation":
                    actual_field = ir.field
                fok, fmsg = check("field", actual_field, exp_field)
                all_ok = all_ok and fok
                print(fmsg)

            if exp_op is not None:
                actual_op = ir.operator
                if ir.type == "conditional_required_field" and isinstance(ir.condition, dict):
                    actual_op = ir.condition.get("operator")
                ook, omsg = check("operator", actual_op, exp_op)
                all_ok = all_ok and ook
                print(omsg)

            if exp_val is not None:
                actual_val = ir.value
                if ir.type == "conditional_required_field" and isinstance(ir.condition, dict):
                    actual_val = ir.condition.get("value")
                vok, vmsg = check("value", actual_val, exp_val)
                all_ok = all_ok and vok
                print(vmsg)

            try:
                xslt = gen.generate(r)
                if ir.type != "unknown" and ("unsupported IR type" in xslt or "<Warning>" in xslt):
                    all_ok = False
                    print("    [FAIL] XSLT: contains unsupported-type warning")
                else:
                    print(f"    [PASS] XSLT: {len(xslt)} chars generated")
            except Exception as xe:
                all_ok = False
                print(f"    [FAIL] XSLT error: {xe}")

            status = "-> PASS" if all_ok else "-> FAIL"
            if all_ok:
                passed += 1
            else:
                failures.append(rule_text)
            print(f"  {status}\n{SEP}")

        except Exception as e:
            import traceback
            failures.append(rule_text)
            traceback.print_exc()
            print(f"  -> FAIL\n{SEP}")

    pct = passed / total * 100
    print(f"\n{'='*60}")
    print(f"  Result: {passed}/{total} ({pct:.1f}%) passed")
    if failures:
        print(f"\n  Failed:")
        for f in failures:
            print(f"    - {f!r}")
    print(f"{'='*60}\n")

    # ── context pollution test ────────────────────────────────────────────
    print("-- Conversation Context Pollution Test --")
    from engine.chat_engine import ChatEngine
    engine = ChatEngine()
    sid = "test-sess"
    engine.get_or_create_session(sid)

    r1 = engine.process_message(sid, "Invoice date should not exceed current date")
    print(f"  User : 'Invoice date should not exceed current date'")
    print(f"  Bot  : {r1.message!r}  status={r1.status}")

    r2 = engine.process_message(sid, "yes")
    print(f"  User : 'yes'")
    print(f"  Bot  : {r2.message!r}  finalized={r2.finalized_rule!r}")

    sess = engine._session(sid)
    rule_parts = sess.rule_parts
    pollution = any("yes" in p.lower() for p in rule_parts)
    print(f"  rule_parts: {rule_parts}")
    print(f"  Context pollution: {'YES - BUG!' if pollution else 'NONE - OK'}")
    if r2.finalized_rule and "yes" in r2.finalized_rule.lower():
        print("  [FAIL] 'yes' found in finalized_rule!")
    else:
        print("  [PASS] finalized_rule is clean")
    print()
    return pct


if __name__ == "__main__":
    accuracy = run()
    sys.exit(0 if accuracy >= 90.9 else 1)
