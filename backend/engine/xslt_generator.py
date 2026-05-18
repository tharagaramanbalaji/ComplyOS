"""
XSLTGenerator – deterministic XSLT generation from ParsedRule IR nodes.

Key fix: conditional_required_field.condition is now a DICT
  {"field": "tax_amount", "operator": ">", "value": 100}
not a raw string.  All XSLT patterns follow the spec examples in the
system requirements.
"""
import re
from typing import List

from schemas.schema import ParsedRule


_OP_XML = {">": "&gt;", "<": "&lt;", ">=": "&gt;=", "<=": "&lt;=", "==": "=", "!=": "!="}


def _xml_op(op: str) -> str:
    return _OP_XML.get(op, op)


class XSLTGenerator:
    """Generates deterministic XSLT from intermediate representation (IR)."""

    # ── XPath registry ────────────────────────────────────────────────────

    _XPATH: dict = {
        "invoice_id":         "(//cbc:ID | //InvoiceID)[1]",
        "issue_date":         "(//cbc:IssueDate | //IssueDate)[1]",
        "buyer_name":         "(//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name | //BuyerName)[1]",
        "seller_name":        "(//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name | //SellerName)[1]",
        "payable_amount":     "(//cbc:PayableAmount | //PayableAmount)[1]",
        "tax_amount":         "(//cbc:TaxAmount | //TaxAmount)[1]",
        "taxable_amount":     "(//cbc:TaxableAmount | //TaxableAmount)[1]",
        "tax_category":       "(//cac:TaxCategory/cbc:ID | //TaxCategory)[1]",
        "tax_exemption_reason": "(//cbc:TaxExemptionReason | //TaxExemptionReason)[1]",
        "currency_code":      "(//cbc:DocumentCurrencyCode | //CurrencyCode)[1]",
    }

    def _get_xpath(self, field: str) -> str:
        if not field:
            return ""
        field = field.strip().lower()
        if field in self._XPATH:
            return self._XPATH[field]
        clean = field.replace("_", "")
        return f"(//cbc:{clean} | //{clean})[1]"

    # ── per-rule XSLT builders ────────────────────────────────────────────

    def _generate_rule_xslt(self, rule: ParsedRule) -> str:
        ir = rule.structured_IR
        err = rule.expected_error_message
        rt = rule.rule_text

        # ── required_field ──────────────────────────────────────────────
        if ir.type == "required_field":
            xp = self._get_xpath(ir.field)
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="not({xp}) or {xp}=''">
            <Error>{err}</Error>
        </xsl:if>
        <xsl:if test="{xp} and {xp}!=''">
            <Pass>{rt} passed</Pass>
        </xsl:if>
"""

        # ── numeric_comparison ──────────────────────────────────────────
        if ir.type == "numeric_comparison":
            xp = self._get_xpath(ir.field)
            op = _xml_op(ir.operator)
            # The validation fails when the condition is NOT met
            neg_op = _xml_op(self._negate_op(ir.operator))
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="number({xp}) {neg_op} {ir.value}">
            <Error>{err}</Error>
        </xsl:if>
        <xsl:if test="number({xp}) {op} {ir.value}">
            <Pass>{rt} passed</Pass>
        </xsl:if>
"""

        # ── conditional_required_field ──────────────────────────────────
        if ir.type == "conditional_required_field":
            cond = ir.condition  # dict: {field, operator, value}
            if isinstance(cond, dict):
                c_xp = self._get_xpath(cond.get("field", ""))
                c_op = _xml_op(cond.get("operator", ">"))
                c_val = cond.get("value", 0)
            else:
                # Legacy string fallback
                m = re.match(r'(\w+)([><=!]+)(\d+)', str(cond))
                if m:
                    c_xp = self._get_xpath(m.group(1))
                    c_op = _xml_op(m.group(2))
                    c_val = m.group(3)
                else:
                    c_xp, c_op, c_val = "(//unknown)[1]", "&gt;", "0"

            r_xp = self._get_xpath(ir.required_field)
            return f"""
        <!-- Rule: {rt} -->
        <xsl:choose>
            <xsl:when test="number({c_xp}) {c_op} {c_val}">
                <xsl:if test="not({r_xp}) or {r_xp}=''">
                    <Error>{err}</Error>
                </xsl:if>
                <xsl:if test="{r_xp} and {r_xp}!=''">
                    <Pass>{rt} passed</Pass>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <Pass>Condition not triggered for: {rt}</Pass>
            </xsl:otherwise>
        </xsl:choose>
"""

        # ── date_validation ─────────────────────────────────────────────
        if ir.type == "date_validation":
            xp = self._get_xpath(ir.field or "issue_date")
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="{xp} &gt; current-date()">
            <Error>{err}</Error>
        </xsl:if>
        <xsl:if test="not({xp} &gt; current-date())">
            <Pass>{rt} passed</Pass>
        </xsl:if>
"""

        # ── duplicate_field_check ───────────────────────────────────────
        if ir.type == "duplicate_field_check":
            xp = self._get_xpath(ir.field)
            xp_count = xp.replace("[1]", "")
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="count({xp_count}) &gt; 1">
            <Error>{err}</Error>
        </xsl:if>
        <xsl:if test="count({xp_count}) = 1">
            <Pass>{rt} passed</Pass>
        </xsl:if>
"""

        # ── amount_calculation ──────────────────────────────────────────
        if ir.type == "amount_calculation":
            t_xp  = self._get_xpath(getattr(ir, "target_field", ""))
            f1_xp = self._get_xpath(getattr(ir, "field_1", ""))
            f2_xp = self._get_xpath(getattr(ir, "field_2", ""))
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="number({t_xp}) != (number({f1_xp}) + number({f2_xp}))">
            <Error>{err}</Error>
        </xsl:if>
        <xsl:if test="number({t_xp}) = (number({f1_xp}) + number({f2_xp}))">
            <Pass>{rt} passed</Pass>
        </xsl:if>
"""

        # ── currency_consistency ────────────────────────────────────────
        if ir.type == "currency_consistency":
            xp = self._get_xpath("currency_code")
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="not({xp})">
            <Error>{err}</Error>
        </xsl:if>
"""

        # ── tax_category_validation ─────────────────────────────────────
        if ir.type == "tax_category_validation":
            xp = self._get_xpath(ir.field or "tax_category")
            allowed = ["'S'", "'E'", "'Z'", "'O'", "'K'", "'L'", "'M'", "'AE'", "'SE'"]
            # If a specific value was requested, restrict to just that
            if ir.value:
                allowed = [f"'{str(ir.value).upper()}'"]
            cond = " or ".join(f"{xp} = {a}" for a in allowed)
            return f"""
        <!-- Rule: {rt} -->
        <xsl:if test="not({cond})">
            <Error>{err}</Error>
        </xsl:if>
        <xsl:if test="{cond}">
            <Pass>{rt} passed</Pass>
        </xsl:if>
"""

        # ── unknown ─────────────────────────────────────────────────────
        return f"""
        <!-- WARNING: unsupported IR type '{ir.type}' for rule: {rt} -->
        <Warning>Could not generate XSLT for: {rt}</Warning>
"""

    @staticmethod
    def _negate_op(op: str) -> str:
        return {">": "<=", "<": ">=", ">=": "<", "<=": ">", "==": "!=", "!=": "=="}.get(op, op)

    # ── public API ────────────────────────────────────────────────────────

    def generate(self, rule: ParsedRule) -> str:
        return self.generate_multiple([rule])

    def generate_multiple(self, rules: List[ParsedRule]) -> str:
        header = '''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">

    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/">
        <ValidationResult>
'''
        body = "".join(self._generate_rule_xslt(r) for r in rules)

        footer = '''
        </ValidationResult>
    </xsl:template>
</xsl:stylesheet>
'''
        return header + body + footer
