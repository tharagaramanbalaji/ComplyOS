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

from typing import List, Dict, Any

class ChatTurnRequest(BaseModel):
    session_id: str
    user_message: Optional[str] = None
    user_choice: Optional[dict] = None
    action: Optional[str] = None

class QuickReply(BaseModel):
    label: str
    action: str
    value: str

class ChatTurnResponse(BaseModel):
    session_id: str
    status: str
    bot_message: str
    quick_replies: List[QuickReply] = []
    draft_ir: Optional[dict] = None
    cart: List[dict] = []
    compiled_xslt: Optional[str] = None
