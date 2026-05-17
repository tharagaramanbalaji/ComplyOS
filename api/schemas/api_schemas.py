from pydantic import BaseModel
from typing import Optional

class ParseRequest(BaseModel):
    rule_text: str

class ParseResponse(BaseModel):
    json_ir: dict

class CompileRequest(BaseModel):
    json_ir: dict

class CompileResponse(BaseModel):
    xslt_code: str

class MagicResponse(BaseModel):
    original_rule: str
    json_ir: dict
    xslt_code: str
    validation_status: str
    message: Optional[str] = None
