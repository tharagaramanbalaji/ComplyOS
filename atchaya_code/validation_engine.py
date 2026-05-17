from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional
from lxml import etree
import json

from pydantic import parse_obj_as
from schema import RuleModel
from xslt_compiler import XSLTCompiler


class ValidationEngine:
    def __init__(self, rule_mapping_path: str):
        self.rule_map: Dict[str, RuleModel] = {}
        self.compiled_xslt: Dict[str, etree.XSLT] = {}
        self.duplicate_cache: set[str] = set()
        self._load_rules(rule_mapping_path)

    def _load_rules(self, path: str) -> None:
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        for rule_id, rule_data in raw.items():
            rule = parse_obj_as(RuleModel, rule_data)
            self.rule_map[rule_id] = rule
            if rule.rule_type != 'duplicate_field_check' and rule.rule_type != 'date_validation':
                self.compiled_xslt[rule_id] = XSLTCompiler.compile_rule_to_xslt(rule_id, rule)

    def validate_invoice(self, xml_path: str) -> Dict[str, Dict[str, str]]:
        results: Dict[str, Dict[str, str]] = {}

        try:
            xml_doc = etree.parse(xml_path)
        except (etree.XMLSyntaxError, OSError) as exc:
            for rule_id, rule in self.rule_map.items():
                results[rule_id] = {
                    'result': 'FAIL',
                    'trace': f'XML parsing failed: {exc}'
                }
            return results

        invoice_id = self._extract_text(xml_doc, './/invoice_id')
        is_duplicate = invoice_id and invoice_id in self.duplicate_cache
        self.duplicate_cache.add(invoice_id)

        for rule_id, rule in self.rule_map.items():
            if rule.rule_type == 'duplicate_field_check':
                results[rule_id] = self._evaluate_duplicate_rule(rule_id, rule, invoice_id, is_duplicate)
                continue

            if rule.rule_type == 'date_validation':
                results[rule_id] = self._evaluate_date_rule(rule_id, rule, xml_doc)
                continue

            xslt = self.compiled_xslt.get(rule_id)
            if not xslt:
                results[rule_id] = {
                    'result': 'PASS',
                    'trace': 'No XSLT available for this rule.'
                }
                continue

            transformed = xslt(xml_doc)
            result_node = transformed.find('.//status')
            trace_node = transformed.find('.//trace')
            results[rule_id] = {
                'result': (result_node.text if result_node is not None else 'FAIL'),
                'trace': (trace_node.text if trace_node is not None else '')
            }

        return results

    def _evaluate_duplicate_rule(self, rule_id: str, rule: RuleModel, invoice_id: Optional[str], is_duplicate: bool) -> Dict[str, str]:
        if rule.rule_type != 'duplicate_field_check':
            return {'result': 'PASS', 'trace': 'Not a duplicate check.'}

        if rule.field != 'invoice_id':
            return {'result': 'PASS', 'trace': f"Duplicate check for '{rule.field}' is currently only supported on invoice_id."}

        if not invoice_id:
            return {'result': 'FAIL', 'trace': 'Missing invoice_id for duplicate validation.'}

        return {
            'result': 'FAIL' if is_duplicate else 'PASS',
            'trace': 'Duplicate invoice_id detected.' if is_duplicate else 'Unique invoice_id.'
        }

    def _extract_text(self, xml_doc: etree._ElementTree, xpath: str) -> str:
        result = xml_doc.xpath(xpath)
        if isinstance(result, list):
            return result[0].text if result and hasattr(result[0], 'text') else ''
        return str(result)

    def _evaluate_date_rule(self, rule_id: str, rule: RuleModel, xml_doc: etree._ElementTree) -> Dict[str, str]:
        assert rule.rule_type == 'date_validation'
        value = self._extract_text(xml_doc, f".//{rule.field}")
        if not value:
            return {'result': 'PASS', 'trace': f'{rule.field} is missing or empty.'}

        try:
            actual = datetime.strptime(value.strip(), '%Y-%m-%d')
        except ValueError:
            return {'result': 'FAIL', 'trace': f"Invalid date format for {rule.field}: '{value}'."}

        if rule.operator == '<=' and rule.value == 'CURRENT_DATE':
            if actual <= datetime.now():
                return {'result': 'PASS', 'trace': f"{rule.field} is on or before current date."}
            return {'result': 'FAIL', 'trace': f"{rule.field} is in the future: {value}."}

        return {'result': 'PASS', 'trace': f'{rule.field} passed date validation.'}


def load_engine(rule_mapping_path: str = 'rule_mappings_train.json') -> ValidationEngine:
    return ValidationEngine(rule_mapping_path)
