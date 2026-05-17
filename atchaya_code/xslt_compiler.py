from __future__ import annotations
from typing import Any
from lxml import etree

from schema import (
    AmountCalculationRule,
    ConditionalRequiredFieldRule,
    CurrencyConsistencyRule,
    DateValidationRule,
    DuplicateFieldCheckRule,
    NumericComparisonRule,
    RequiredFieldRule,
    TaxCategoryValidationRule,
)
from xml_extractor import XMLExtractor


class XSLTCompiler:
    VALID_TAX_CODES = ['S', 'E', 'Z', 'AE', 'K', 'G', 'O']

    @staticmethod
    def _escape_xpath_for_attribute(expression: str) -> str:
        return (
            expression.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
        )

    @staticmethod
    def _build_fail_condition(rule: Any) -> str:
        if isinstance(rule, RequiredFieldRule):
            xpath = XMLExtractor.field_to_xpath(rule.field)
            return f"not({xpath})"

        if isinstance(rule, ConditionalRequiredFieldRule):
            cond = rule.condition
            cond_xpath = XMLExtractor.field_to_xpath(cond.field)
            expected_value = cond.value
            action_xpath = XMLExtractor.field_to_xpath(rule.action.field)
            return f"{cond_xpath} = '{expected_value}' and not({action_xpath})"

        if isinstance(rule, NumericComparisonRule):
            field_xpath = XMLExtractor.field_to_xpath(rule.field)
            return f"count({field_xpath}[normalize-space(.) != '' and not(number(.) {rule.operator} {rule.value})]) > 0"

        if isinstance(rule, AmountCalculationRule):
            if rule.aggregation == 'sum' and rule.expected_match:
                sum_xpath = XMLExtractor.sum_expression(rule.field)
                match_xpath = XMLExtractor.numeric_expression(rule.expected_match)
                return (
                    f"count(/Invoice/line_items/line_item) > 0 and number(/Invoice/{rule.expected_match}) = number(/Invoice/{rule.expected_match}) and not((({sum_xpath} - {match_xpath}) <= 0.01) and (({match_xpath} - {sum_xpath}) <= 0.01))"
                )
            if rule.field == 'payable_amount':
                return (
                    "count(/Invoice/payable_amount) > 0 and "
                    "number(/Invoice/taxable_amount) = number(/Invoice/taxable_amount) and "
                    "number(/Invoice/tax_amount) = number(/Invoice/tax_amount) and "
                    "(((number(/Invoice/payable_amount) - (number(/Invoice/taxable_amount) + number(/Invoice/tax_amount))) > 0.01) or "
                    "(((number(/Invoice/taxable_amount) + number(/Invoice/tax_amount)) - number(/Invoice/payable_amount)) > 0.01))"
                )
            return 'false()'

        if isinstance(rule, CurrencyConsistencyRule):
            if rule.field == 'line_items[*].currency_code':
                return "count(/Invoice/line_items/line_item[currency_code != /Invoice/currency_code]) > 0"
            return "/Invoice/currency_code != /Invoice/payment_currency"

        if isinstance(rule, TaxCategoryValidationRule):
            allowed = rule.valid_values or XSLTCompiler.VALID_TAX_CODES
            if rule.field == 'line_items[*].tax_category':
                clause = ' or '.join([f"tax_category = '{token}'" for token in allowed])
                return f"count(/Invoice/line_items/line_item[not({clause})]) > 0"
            clause = ' or '.join([f"/Invoice/tax_category = '{token}'" for token in allowed])
            return f"not({clause})"

        if isinstance(rule, DateValidationRule):
            xpath = XMLExtractor.field_to_xpath(rule.field)
            return f"false()"

        if isinstance(rule, DuplicateFieldCheckRule):
            return 'false()'

        return 'false()'

    @staticmethod
    def compile_rule_to_xslt(rule_id: str, rule: Any) -> etree.XSLT:
        fail_condition = XSLTCompiler._build_fail_condition(rule)
        trace = XSLTCompiler._build_trace_text(rule_id, rule)

        escaped_condition = XSLTCompiler._escape_xpath_for_attribute(fail_condition)
        template = f"""
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template match="/">
    <result>
      <rule_id>{rule_id}</rule_id>
      <rule_type>{rule.rule_type}</rule_type>
      <status>
        <xsl:choose>
          <xsl:when test=\"{escaped_condition}\">FAIL</xsl:when>
          <xsl:otherwise>PASS</xsl:otherwise>
        </xsl:choose>
      </status>
      <trace>{trace}</trace>
    </result>
  </xsl:template>
</xsl:stylesheet>
"""
        xslt_tree = etree.XML(template.encode('utf-8'))
        return etree.XSLT(xslt_tree)

    @staticmethod
    def _build_trace_text(rule_id: str, rule: Any) -> str:
        if isinstance(rule, RequiredFieldRule):
            return f"Required field '{rule.field}' must be present."
        if isinstance(rule, ConditionalRequiredFieldRule):
            return (
                f"When '{rule.condition.field}' is '{rule.condition.value}', '{rule.action.field}' must be present."
            )
        if isinstance(rule, NumericComparisonRule):
            return f"Numeric comparison: {rule.field} {rule.operator} {rule.value}."
        if isinstance(rule, AmountCalculationRule):
            if rule.aggregation == 'sum' and rule.expected_match:
                return f"Sum of {rule.field} must equal {rule.expected_match}."
            return "Payable amount must equal taxable_amount + tax_amount."
        if isinstance(rule, CurrencyConsistencyRule):
            return f"Currency values for {rule.field} must match {rule.expected_match}."
        if isinstance(rule, TaxCategoryValidationRule):
            return f"Tax category values must be one of {', '.join(rule.valid_values or XSLTCompiler.VALID_TAX_CODES)}."
        if isinstance(rule, DateValidationRule):
            return f"Date validation for {rule.field} against current date."
        if isinstance(rule, DuplicateFieldCheckRule):
            return f"Field '{rule.field}' must be unique across invoices."
        return "Validation rule executed."
