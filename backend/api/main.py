from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json

from schemas.schema import ParsedRule, ValidationResult
from parser.rule_parser import RuleParser
from engine.validator import Validator
from engine.xslt_generator import XSLTGenerator
from engine.chat_engine import ChatEngine
from schemas.schema import ChatMessage, ChatResponse, ChatContext

app = FastAPI(title="ComplyOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = RuleParser()
xslt_gen = XSLTGenerator()
chat_engine = ChatEngine()

# In-memory storage for demo
rules_store: List[ParsedRule] = []

@app.post("/api/rules/parse", response_model=List[ParsedRule])
def parse_rule(rule_text: str = Form(...), severity: str = Form("ERROR"), expected_error: str = Form("")):
    parsed_rules = parser.parse(rule_text, severity, expected_error)
    if not isinstance(parsed_rules, list):
        parsed_rules = [parsed_rules]
    for p in parsed_rules:
        rules_store.append(p)
    return parsed_rules

@app.get("/api/rules", response_model=List[ParsedRule])
def get_rules():
    return rules_store

@app.post("/api/validate", response_model=ValidationResult)
async def validate_invoice(
    file: UploadFile = File(...),
    rule_id: Optional[str] = Form(None),
    rule_text: Optional[str] = Form(None),
    severity: Optional[str] = Form(None),
    rule_type: Optional[str] = Form(None),
    structured_IR: Optional[str] = Form(None)
):
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Only XML files are supported")
    
    if not rule_id or not structured_IR:
        raise HTTPException(status_code=400, detail="No active rule selected. Please provide rule payload.")
    
    content = await file.read()
    
    try:
        from schemas.schema import IRNode
        ir_dict_list = json.loads(structured_IR)
        if not isinstance(ir_dict_list, list):
            ir_dict_list = [ir_dict_list]
        
        parsed_rules = []
        for i, ir_dict in enumerate(ir_dict_list):
            ir_node = IRNode(**ir_dict)
            parsed_rules.append(ParsedRule(
                rule_id=f"{rule_id}_{i}",
                rule_text=rule_text or "",
                severity=severity or "ERROR",
                expected_error_message=f"Validation failed for {rule_type}",
                rule_type=rule_type or "unknown",
                structured_IR=ir_node,
                parsed_entities={}
            ))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse rule payload: {str(e)}")

    validator = Validator(parsed_rules)
    result = validator.validate(content)
    return result

@app.post("/api/xslt")
def generate_xslt(rule_id: str):
    # Rule id can be a comma separated list
    ids = rule_id.split(",")
    rules = [r for r in rules_store if r.rule_id in ids]
    if not rules:
        raise HTTPException(status_code=404, detail="Rules not found")
    
    xslt = xslt_gen.generate_multiple(rules)
    return {"xslt": xslt}

@app.get("/api/stats")
def get_stats():
    return {
        "total_rules": len(rules_store),
        "rule_types": list(set(r.rule_type for r in rules_store)),
        "system_status": "Operational"
    }

@app.post("/api/chat/start", response_model=ChatContext)
def start_chat(session_id: str = Form(...)):
    return chat_engine.get_or_create_session(session_id)

@app.post("/api/chat/message", response_model=ChatResponse)
def send_chat_message(msg: ChatMessage):
    return chat_engine.process_message(
        msg.conversation_id, 
        msg.text, 
        msg.is_clarification_response, 
        msg.clarification_type
    )

@app.get("/api/chat/history", response_model=ChatContext)
def get_chat_history(session_id: str):
    return chat_engine.get_or_create_session(session_id)

@app.post("/api/chat/resolve")
def resolve_chat(session_id: str = Form(...)):
    rule = chat_engine.resolve_conversation(session_id)
    return {"finalized_rule": rule}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
