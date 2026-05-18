import asyncio
from api.main import parse_rule, validate_invoice, generate_xslt, get_rules
import io

async def test():
    print("Testing Parse Rule...")
    r1 = parse_rule(rule_text="Tax amount should be greater than 0", severity="ERROR", expected_error="")
    print(r1.model_dump_json(indent=2))

    r2 = parse_rule(rule_text="If tax amount > 0 tax category required", severity="ERROR", expected_error="")
    print(r2.model_dump_json(indent=2))

    print("\nTesting Generate XSLT...")
    try:
        xslt_res = generate_xslt(r1.rule_id)
        print("XSLT for r1:", xslt_res)
    except Exception as e:
        print("Error generating XSLT:", e)

    # Test Validation
    xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
    <Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
        xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
        <cbc:ID>INV-123</cbc:ID>
        <cac:TaxTotal>
            <cbc:TaxAmount>10.00</cbc:TaxAmount>
            <cac:TaxSubtotal>
                <cac:TaxCategory>
                    <cbc:ID>S</cbc:ID>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>
    </Invoice>'''

    class MockUploadFile:
        def __init__(self, content):
            self.content = content
            self.filename = "test.xml"
        async def read(self):
            return self.content

    f = MockUploadFile(xml_content)
    print("\nTesting Validate Invoice...")
    try:
        val_res = await validate_invoice(f)
        print(val_res.model_dump_json(indent=2))
    except Exception as e:
        print("Validation Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
