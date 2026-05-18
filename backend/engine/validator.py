from typing import List, Any
from schemas.schema import ParsedRule, ValidationResult
from xml_processor.xml_reader import XMLReader
from engine.rule_executor import RuleExecutor

class Validator:
    def __init__(self, rules: List[ParsedRule]):
        self.rules = rules
        self.executor = RuleExecutor()

    def validate(self, xml_content: bytes) -> ValidationResult:
        try:
            reader = XMLReader(xml_content)
            extracted_data = reader.extract_invoice_data()
        except Exception as e:
            return ValidationResult(
                invoice_id=None,
                pass_fail="FAIL",
                validation_errors=[{"rule_id": "SYS", "message": f"XML Parsing Error: {str(e)}", "severity": "FATAL"}],
                trace=[],
                severity="FATAL"
            )

        traces = []
        errors = []
        all_passed = True
        highest_severity = "PASS"

        for rule in self.rules:
            passed, trace, error = self.executor.execute(rule, extracted_data)
            traces.append(trace)
            if not passed:
                all_passed = False
                errors.append(error)
                if error.severity == "FATAL":
                    highest_severity = "FATAL"
                elif error.severity == "ERROR" and highest_severity != "FATAL":
                    highest_severity = "ERROR"
                elif error.severity == "WARNING" and highest_severity not in ["FATAL", "ERROR"]:
                    highest_severity = "WARNING"

        return ValidationResult(
            invoice_id=extracted_data.get("invoice_id", "UNKNOWN"),
            pass_fail="PASS" if all_passed else "FAIL",
            validation_errors=errors,
            trace=traces,
            severity=highest_severity if not all_passed else "PASS"
        )
