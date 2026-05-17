from datetime import datetime

def field_to_xpath(field: str) -> str:
    """Helper to convert JSON IR field paths to valid XML XPath queries."""
    if field == "line_items[*].amount":
        return "/Invoice/line_items/line_item/amount"
    if field == "line_items[*].currency_code":
        return "/Invoice/line_items/line_item/currency_code"
    if field == "line_items[*].tax_category":
        return "/Invoice/line_items/line_item/tax_category"
    return f"/Invoice/{field}"

def compile_rule_to_xslt(rule_ir: dict) -> str:
    """
    Takes a parsed JSON IR dictionary and compiles it into an executable XSLT script.
    This acts as the bridge between Semantic NLP and Deterministic XML Execution.
    """
    r_type = rule_ir.get("rule_type")
    
    # Construct the core XPath test condition. Default to fail if unknown.
    test_condition = "false()" 
    
    if r_type == "required_field":
        xpath = field_to_xpath(rule_ir["field"])
        test_condition = f"string-length({xpath}) &gt; 0"
        
    elif r_type == "conditional_required_field":
        cond_field = field_to_xpath(rule_ir.get("condition_field", ""))
        cond_val = rule_ir.get("condition_value", "")
        act_field = field_to_xpath(rule_ir.get("field", ""))
        # If condition is not met, PASS. If met, check action field exists
        test_condition = f"not({cond_field} = '{cond_val}') or string-length({act_field}) &gt; 0"
        
    elif r_type == "numeric_comparison":
        xpath = field_to_xpath(rule_ir["field"])
        op = rule_ir["operator"]
        val = rule_ir["value"]
        # Convert operators to be XML safe
        op_xml = op.replace(">", "&gt;").replace("<", "&lt;")
        test_condition = f"number({xpath}) {op_xml} {val}"
        
    elif r_type == "amount_calculation":
        if rule_ir["field"] == "payable_amount":
            pay = field_to_xpath("payable_amount")
            taxable = field_to_xpath("taxable_amount")
            tax = field_to_xpath("tax_amount")
            # Math execution in XPath
            test_condition = f"number({pay}) = (number({taxable}) + number({tax}))"
        elif rule_ir.get("aggregation") == "sum":
            lines_xpath = field_to_xpath(rule_ir["field"])
            match_xpath = field_to_xpath(rule_ir["expected_match"])
            test_condition = f"sum({lines_xpath}) = number({match_xpath})"
            
    elif r_type == "currency_consistency":
        xpath = field_to_xpath(rule_ir["field"])
        match_xpath = field_to_xpath(rule_ir["expected_match"])
        # Check if 0 nodes exist that don't match the expected currency
        test_condition = f"count({xpath}[. != {match_xpath}]) = 0"
        
    elif r_type == "tax_category_validation":
        xpath = field_to_xpath(rule_ir["field"])
        valid_vals = rule_ir["valid_values"]
        # Create an OR condition for all valid values
        conds = " or ".join([f". = '{v}'" for v in valid_vals])
        test_condition = f"count({xpath}[not({conds})]) = 0"
        
    elif r_type == "date_validation":
        xpath = field_to_xpath(rule_ir["field"])
        # Hacky but standard XSLT 1.0 way to compare ISO dates (YYYY-MM-DD string comparison)
        today = datetime.now().strftime('%Y-%m-%d')
        test_condition = f"{xpath} &lt;= '{today}'"
        
    elif r_type == "duplicate_field_check":
        # XSLT evaluates a single document. It cannot check across a database of multiple files for uniqueness.
        # This highlights a fundamental limitation of pure XSLT for cross-document state.
        # We will let it pass here, and handle uniqueness in the Python API wrapper.
        test_condition = "true()"

    # Wrap the logic in the standard XSLT 1.0 Boilerplate
    xslt_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" />
    <xsl:template match="/">
        <xsl:choose>
            <xsl:when test="{test_condition}">PASS</xsl:when>
            <xsl:otherwise>FAIL</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
'''
    return xslt_template
