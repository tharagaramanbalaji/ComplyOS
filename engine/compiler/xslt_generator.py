from datetime import datetime

def field_to_xpath(field: str) -> str:
    """Helper to convert JSON IR field paths to valid XML XPath queries."""
    if field == "line_items":
        return "/Invoice/line_items"
    if "[*]" in field:
        segments = field.split('.')
        xpath_parts = ["/Invoice"]
        for segment in segments:
            if segment.endswith('[*]'):
                container = segment[:-3]
                xpath_parts.append(f"{container}/line_item")
            else:
                xpath_parts.append(segment)
        return '/'.join(xpath_parts)
    return f"/Invoice/{field}"

def get_xpath_condition(rule_ir: dict) -> str:
    r_type = rule_ir.get("rule_type")
    test_condition = "false()"
    
    if r_type == "required_field":
        xpath = field_to_xpath(rule_ir["field"])
        test_condition = f"count({xpath}) &gt; 0"
        
    elif r_type == "conditional_required_field":
        cond = rule_ir.get("condition", {})
        act = rule_ir.get("action", {})
        cond_field_raw = cond.get("field") or rule_ir.get("condition_field", "")
        cond_val_raw = cond.get("value") or rule_ir.get("condition_value", "")
        act_field_raw = act.get("field") or rule_ir.get("field", "")
        
        cond_field = field_to_xpath(cond_field_raw)
        act_field = field_to_xpath(act_field_raw)
        
        val_map = {"Exempt": "E", "Standard": "S", "Zero": "Z", "US": "US"}
        cond_val = val_map.get(str(cond_val_raw), str(cond_val_raw))
        
        test_condition = f"not({cond_field} = '{cond_val}') or count({act_field}) &gt; 0"
        
    elif r_type == "numeric_comparison":
        xpath = field_to_xpath(rule_ir["field"])
        op = rule_ir.get("operator", "&gt;=")
        val = rule_ir.get("value", 0)
        op_xml = op.replace(">", "&gt;").replace("<", "&lt;")
        if "line_item" in xpath:
            test_condition = f"count({xpath}[not(number(.) {op_xml} {val})]) = 0"
        else:
            test_condition = f"not({xpath}) or (number({xpath}) {op_xml} {val})"
        
    elif r_type == "amount_calculation":
        pay = field_to_xpath(rule_ir["field"])
        if rule_ir.get("equation"):
            eq = rule_ir["equation"]
            for f_name in ["taxable_amount", "tax_amount", "payable_amount"]:
                if f_name in eq:
                    eq = eq.replace(f_name, f"number({field_to_xpath(f_name)})")
            taxable = field_to_xpath("taxable_amount")
            tax = field_to_xpath("tax_amount")
            test_condition = f"not({pay}) or not({taxable}) or not({tax}) or (round(number({pay}) * 100) = round(({eq}) * 100))"
        elif rule_ir.get("field") == "payable_amount":
            pay = field_to_xpath("payable_amount")
            taxable = field_to_xpath("taxable_amount")
            tax = field_to_xpath("tax_amount")
            test_condition = f"not({pay}) or not({taxable}) or not({tax}) or (round(number({pay}) * 100) = round((number({taxable}) + number({tax})) * 100))"
        elif rule_ir.get("aggregation") == "sum":
            lines_xpath = field_to_xpath(rule_ir["field"])
            match_xpath = field_to_xpath(rule_ir.get("expected_match", "taxable_amount"))
            test_condition = f"not({lines_xpath}) or not({match_xpath}) or (round(sum({lines_xpath}) * 100) = round(number({match_xpath}) * 100))"
            
    elif r_type == "currency_consistency":
        xpath = field_to_xpath(rule_ir["field"])
        match_raw = rule_ir.get("expected_match", "currency_code")
        if match_raw in ["currency_code", "payment_currency"]:
            match_xpath = field_to_xpath(match_raw)
        else:
            match_xpath = f"'{match_raw}'"
        test_condition = f"not({xpath}) or not({match_xpath}) or count({xpath}[. != {match_xpath}]) = 0"
        
    elif r_type == "tax_category_validation":
        xpath = field_to_xpath(rule_ir["field"])
        valid_vals = rule_ir.get("valid_values") or rule_ir.get("allowed_values") or ["S", "E", "Z", "AE", "K", "G", "O"]
        conds = " or ".join([f". = '{v}'" for v in valid_vals])
        test_condition = f"not({xpath}) or count({xpath}[not({conds})]) = 0"
        
    elif r_type == "date_validation":
        xpath = field_to_xpath(rule_ir["field"])
        today = datetime.now().strftime('%Y-%m-%d')
        op = rule_ir.get("operator", "<=")
        op_xml = op.replace(">", "&gt;").replace("<", "&lt;")
        today_num = today.replace('-', '')
        test_condition = f"not({xpath}) or (number(translate({xpath}, '-', '')) {op_xml} {today_num})"
        
    elif r_type == "duplicate_field_check":
        test_condition = "true()"
        
    return test_condition

def compile_rule_to_xslt(rule_ir: dict) -> str:
    """Takes a parsed JSON IR dictionary and compiles it into an executable XSLT script."""
    test_condition = get_xpath_condition(rule_ir)
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

def compile_bundle_to_xslt(rule_irs: list) -> str:
    """Takes a list of JSON IR dictionaries and compiles them into a unified multi-rule XSLT bundle with granular tracing."""
    if not rule_irs:
        return compile_rule_to_xslt({"rule_type": "duplicate_field_check"})
    
    var_defs = []
    var_names = []
    checks = []
    
    for idx, ir in enumerate(rule_irs):
        v_name = f"r{idx+1}"
        cond = get_xpath_condition(ir)
        var_defs.append(f'        <xsl:variable name="{v_name}" select="{cond}" />')
        var_names.append(f"${v_name}")
        
        r_type = ir.get("rule_type", f"rule_{idx+1}")
        checks.append(f'''        <xsl:choose>
            <xsl:when test="${v_name}">[PASS] Rule {idx+1} ({r_type})&#10;</xsl:when>
            <xsl:otherwise>[FAIL] Rule {idx+1} ({r_type})&#10;</xsl:otherwise>
        </xsl:choose>''')

    master_cond = " and ".join(var_names)
    var_defs_str = "\n".join(var_defs)
    checks_str = "\n".join(checks)
    
    xslt_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="text" />
    <xsl:template match="/">
{var_defs_str}
        <xsl:choose>
            <xsl:when test="{master_cond}">BUNDLE_PASS&#10;</xsl:when>
            <xsl:otherwise>BUNDLE_FAIL&#10;</xsl:otherwise>
        </xsl:choose>
{checks_str}
    </xsl:template>
</xsl:stylesheet>
'''
    return xslt_template
