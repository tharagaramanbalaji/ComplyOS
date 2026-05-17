from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from api.schemas.api_schemas import MagicResponse, ParseRequest, ParseResponse, CompileRequest, CompileResponse
from api.core.dependencies import get_parser
from engine.compiler.xslt_generator import compile_rule_to_xslt
from engine.executor.validator import execute_xslt

router = APIRouter()

# --- STEP-BY-STEP ENDPOINTS FOR DEMO ---

@router.post("/parse", response_model=ParseResponse)
async def parse_rule(request: ParseRequest, parser = Depends(get_parser)):
    try:
        json_ir = parser.parse_rule(request.rule_text)
        return ParseResponse(json_ir=json_ir)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/compile", response_model=CompileResponse)
async def compile_rule(request: CompileRequest):
    try:
        xslt_code = compile_rule_to_xslt(request.json_ir)
        return CompileResponse(xslt_code=xslt_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from lxml import etree

# Global in-memory cache for duplicate tracking during the hackathon demo
DUPLICATE_CACHE = set()

@router.post("/execute")
async def execute_validation(
    xslt_code: str = Form(...),
    json_ir_str: str = Form(""),
    invoice_file: UploadFile = File(...)
):
    if not invoice_file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Must be an XML file")
    try:
        xml_content = await invoice_file.read()
        xml_string = xml_content.decode("utf-8")
        result = execute_xslt(xml_string, xslt_code)
        
        # --- Python-Level Duplicate Invoice Check ---
        import json
        if json_ir_str:
            ir = json.loads(json_ir_str)
            if ir.get("rule_type") == "duplicate_field_check":
                field = ir.get("field", "invoice_id")
                # Parse XML to find the value
                doc = etree.fromstring(xml_content)
                nodes = doc.xpath(f"//Invoice/{field} | //*[local-name()='{field}']")
                if nodes and nodes[0].text:
                    val = nodes[0].text
                    if val in DUPLICATE_CACHE:
                        result = "FAIL"  # Override the XSLT Pass
                    else:
                        DUPLICATE_CACHE.add(val)
        
        return {"validation_status": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- THE ALL-IN-ONE ENDPOINT ---

@router.post("/magic", response_model=MagicResponse)
async def magic_validation(
    rule_text: str = Form(...),
    invoice_file: UploadFile = File(...),
    parser = Depends(get_parser)
):
    if not invoice_file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Must be an XML file")
    try:
        xml_content = await invoice_file.read()
        xml_string = xml_content.decode("utf-8")
        json_ir = parser.parse_rule(rule_text)
        xslt_code = compile_rule_to_xslt(json_ir)
        result = execute_xslt(xml_string, xslt_code)
        
        # --- Python-Level Duplicate Invoice Check ---
        if json_ir.get("rule_type") == "duplicate_field_check":
            field = json_ir.get("field", "invoice_id")
            doc = etree.fromstring(xml_content)
            nodes = doc.xpath(f"//Invoice/{field} | //*[local-name()='{field}']")
            if nodes and nodes[0].text:
                val = nodes[0].text
                if val in DUPLICATE_CACHE:
                    result = "FAIL"
                else:
                    DUPLICATE_CACHE.add(val)
                    
        return MagicResponse(
            original_rule=rule_text,
            json_ir=json_ir,
            xslt_code=xslt_code.strip(),
            validation_status=result,
            message="Success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
