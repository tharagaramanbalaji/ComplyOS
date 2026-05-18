from typing import List, Optional, Any, Dict
from pydantic import BaseModel

class IRNode(BaseModel):
    type: str
    condition: Optional[Any] = None
    required_field: Optional[str] = None
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    target_field: Optional[str] = None

class ParsedRule(BaseModel):
    rule_id: str
    rule_text: str
    rule_type: str
    severity: str
    expected_error_message: str
    structured_IR: IRNode
    parsed_entities: Dict[str, Any]

class ValidationError(BaseModel):
    rule_id: str
    message: str
    severity: str

class ValidationTrace(BaseModel):
    rule_id: str
    rule_text: str
    passed: bool
    evaluation_details: str

class ValidationResult(BaseModel):
    invoice_id: Optional[str]
    pass_fail: str
    validation_errors: List[ValidationError]
    trace: List[ValidationTrace]
    severity: str # e.g. "ERROR", "WARNING", "PASS"

class ChatContext(BaseModel):
    conversation_id: str
    active_entities: Dict[str, Any] = {}
    partial_rules: List[str] = []
    clarifications: List[Dict[str, Any]] = []
    selected_values: Dict[str, str] = {}
    pending_questions: List[Dict[str, Any]] = []
    status: str = "active"
    finalized_rule: Optional[str] = None

class ChatMessage(BaseModel):
    conversation_id: str
    text: str
    is_clarification_response: bool = False
    clarification_type: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    options: List[str] = []
    status: str # "clarification_required", "active", "resolved"
    finalized_rule: Optional[str] = None
    clarification_type: Optional[str] = None
    confidence_score: float = 1.0
