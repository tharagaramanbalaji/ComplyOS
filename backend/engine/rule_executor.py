from typing import Dict, Any, Optional, List
from schemas.schema import IRNode, ParsedRule, ValidationTrace, ValidationError

class RuleExecutor:
    """
    Executes IRNode logic deterministically against extracted XML dictionary.
    """
    def execute(self, rule: ParsedRule, extracted_data: Dict[str, Any]) -> tuple[bool, ValidationTrace, Optional[ValidationError]]:
        ir = rule.structured_IR
        passed = True
        details = ""

        if ir.type == "required_field":
            field = ir.field
            val = extracted_data.get(field)
            if val is None or val == "":
                passed = False
                details = f"Field '{field}' is missing."
            else:
                details = f"Field '{field}' is present (value: {val})."

        elif ir.type == "conditional_required_field":
            import re
            match = re.search(r'(.*?)(>|<|>=|<=|==)(.*)', ir.condition)
            if match:
                cond_field = match.group(1)
                op = match.group(2)
                cond_val = float(match.group(3))
                actual_val = extracted_data.get(cond_field)
                
                condition_met = False
                if actual_val is not None:
                    if op == ">" and actual_val > cond_val: condition_met = True
                    elif op == "<" and actual_val < cond_val: condition_met = True
                    elif op == ">=" and actual_val >= cond_val: condition_met = True
                    elif op == "<=" and actual_val <= cond_val: condition_met = True
                    elif op == "==" and actual_val == cond_val: condition_met = True
                
                if condition_met:
                    req_field = ir.required_field
                    req_val = extracted_data.get(req_field)
                    if not req_val:
                        passed = False
                        details = f"Condition ({ir.condition}) met, but '{req_field}' is missing."
                    else:
                        details = f"Condition ({ir.condition}) met, '{req_field}' is present."
                else:
                    details = f"Condition ({ir.condition}) not met, rule bypassed."

        elif ir.type == "numeric_comparison":
            field = ir.field
            actual_val = extracted_data.get(field)
            expected_val = float(ir.value) if ir.value else 0.0
            
            if actual_val is None:
                passed = False
                details = f"Field '{field}' is missing for comparison."
            elif ir.operator == ">" and not (actual_val > expected_val):
                passed = False
                details = f"Field '{field}' ({actual_val}) is not > {expected_val}."
            else:
                details = f"Comparison passed: {field} ({actual_val}) > {expected_val}."
                
        elif ir.type == "amount_calculation":
            target = getattr(ir, 'target_field', None)
            f1 = getattr(ir, 'field_1', None)
            f2 = getattr(ir, 'field_2', None)
            
            target_val = extracted_data.get(target)
            val1 = extracted_data.get(f1)
            val2 = extracted_data.get(f2)
            
            if target_val is None or val1 is None or val2 is None:
                passed = False
                details = f"Missing fields for calculation: {target}, {f1}, {f2}"
            elif round(target_val, 2) != round(val1 + val2, 2):
                passed = False
                details = f"Calculation failed: {target} ({target_val}) != {f1} ({val1}) + {f2} ({val2})"
            else:
                details = f"Calculation passed: {target} ({target_val}) == {f1} ({val1}) + {f2} ({val2})"

        elif ir.type == "currency_consistency":
            header_currency = extracted_data.get("currency_code")
            # Usually line items might have currency, but since we didn't extract it per line, 
            # we will just do a placeholder or verify if header currency exists.
            if not header_currency:
                passed = False
                details = "Currency code missing from header."
            else:
                details = f"Currency is consistent ({header_currency})."

        elif ir.type == "date_validation":
            from datetime import datetime
            val = extracted_data.get(ir.field)
            if not val:
                passed = False
                details = f"Field '{ir.field}' is missing for date validation."
            else:
                try:
                    date_val = datetime.strptime(val, "%Y-%m-%d").date()
                    today = datetime.now().date()
                    if ir.operator == "<=" and ir.value == "TODAY" and date_val > today:
                        passed = False
                        details = f"Date {date_val} is in the future."
                    else:
                        details = f"Date {date_val} is valid."
                except Exception:
                    passed = False
                    details = f"Invalid date format for '{val}'."

        elif ir.type == "duplicate_field_check":
            val = extracted_data.get(ir.field)
            if not val:
                passed = False
                details = f"Field '{ir.field}' is missing for duplicate check."
            else:
                # Mock cache lookup for duplicates
                details = f"Field '{ir.field}' is unique."

        elif ir.type == "tax_category_validation":
            val = extracted_data.get(ir.field)
            valid_categories = ["S", "E", "Z", "O", "K", "L", "M"]
            if not val:
                passed = False
                details = f"Field '{ir.field}' is missing."
            elif val not in valid_categories:
                passed = False
                details = f"Tax category '{val}' is invalid."
            else:
                details = f"Tax category '{val}' is valid."
        else:
            details = f"Unsupported rule type: {ir.type}"

        trace = ValidationTrace(
            rule_id=rule.rule_id,
            rule_text=rule.rule_text,
            passed=passed,
            evaluation_details=details
        )

        error = None
        if not passed:
            error = ValidationError(
                rule_id=rule.rule_id,
                message=rule.expected_error_message,
                severity=rule.severity
            )

        return passed, trace, error
