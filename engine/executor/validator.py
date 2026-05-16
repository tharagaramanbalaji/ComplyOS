from lxml import etree
import io

def execute_xslt(xml_content: str, xslt_content: str) -> str:
    """
    Takes an XML invoice string and an XSLT script string.
    Executes the XSLT transformation natively using lxml and returns the result.
    Expected output: 'PASS' or 'FAIL'
    """
    try:
        # 1. Parse the XML invoice into an lxml ElementTree
        xml_doc = etree.parse(io.BytesIO(xml_content.encode('utf-8')))
        
        # 2. Parse the auto-generated XSLT script
        xslt_doc = etree.parse(io.BytesIO(xslt_content.encode('utf-8')))
        transform = etree.XSLT(xslt_doc)
        
        # 3. Execute the XSLT validation deterministically
        result_tree = transform(xml_doc)
        
        # 4. Return the result (stripping any stray XML formatting/newlines)
        return str(result_tree).strip()
        
    except Exception as e:
        # If the XML is malformed or XSLT crashes, we catch it here.
        # In Phase 4, this exception will feed directly into our Explainability Trace System.
        return f"FAIL (Execution Error: {str(e)})"
