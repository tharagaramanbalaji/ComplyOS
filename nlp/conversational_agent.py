from nlp.parser import NLPRuleParser
from engine.compiler.xslt_generator import compile_bundle_to_xslt, compile_rule_to_xslt
import uuid

# Global in-memory session store for multi-turn state retention
SESSION_STORE = {}

class ConversationalCopilot:
    def __init__(self):
        self.parser = NLPRuleParser()
        
    def process_turn(self, session_id: str, user_message: str = None, user_choice: dict = None, action: str = None) -> dict:
        if session_id not in SESSION_STORE:
            SESSION_STORE[session_id] = {
                "history": [],
                "cart": [],
                "draft_ir": None,
                "status": "ready"
            }
        session = SESSION_STORE[session_id]
        
        # Handle explicit cart actions
        if action == "clear_cart":
            session["cart"] = []
            session["status"] = "ready"
            session["draft_ir"] = None
            return {"session_id": session_id, "status": "ready", "bot_message": "Compliance bundle cleared. You can start building a new rule bundle.", "cart": [], "quick_replies": []}
            
        if action == "compile_cart":
            if not session["cart"]:
                return {"session_id": session_id, "status": "ready", "bot_message": "Your compliance bundle is currently empty.", "cart": [], "quick_replies": []}
            xslt = compile_bundle_to_xslt(session["cart"])
            session["status"] = "ready"
            return {
                "session_id": session_id, 
                "status": "ready", 
                "bot_message": f"Successfully compiled {len(session['cart'])} rules into a unified Master Compliance Bundle!", 
                "cart": session["cart"], 
                "compiled_xslt": xslt.strip(), 
                "quick_replies": []
            }

        # Handle quick-reply interactive choices
        if user_choice:
            draft = session.get("draft_ir")
            if draft:
                act = user_choice.get("action")
                val = user_choice.get("value")
                if act == "add_value":
                    if "valid_values" not in draft: draft["valid_values"] = ["S", "E", "Z", "O"]
                    if val not in draft["valid_values"]: draft["valid_values"].append(val)
                elif act == "replace_value":
                    draft["valid_values"] = [val]
                elif act == "set_field":
                    draft["field"] = val
                    
                session["cart"].append(draft)
                session["draft_ir"] = None
                session["status"] = "ready"
                xslt = compile_bundle_to_xslt(session["cart"])
                return {
                    "session_id": session_id, 
                    "status": "ready", 
                    "bot_message": f"Rule confirmed and added to your Compliance Bundle! Total rules in bundle: {len(session['cart'])}.", 
                    "cart": session["cart"], 
                    "compiled_xslt": xslt.strip(),
                    "quick_replies": []
                }

        # Handle new user natural language messages
        if user_message:
            session["history"].append({"role": "user", "content": user_message})
            lower_msg = user_message.lower().strip()
            
            # --- Multi-Turn Rule Continuation Logic ---
            # E.g. User previously added "The tax category must be S or Z"
            # Now user says "also AE is also accepted" or "and K as well"
            is_continuation = any(lower_msg.startswith(w) or f" {w} " in f" {lower_msg} " for w in ["also", "and", "add", "include", "accept", "accepted"])
            if session["cart"] and is_continuation:
                last_rule = session["cart"][-1]
                if last_rule.get("rule_type") == "tax_category_validation":
                    clean_words = [w.strip(".'\",;!?()[]{}") for w in user_message.split()]
                    new_codes = [w.upper() for w in clean_words if len(w) <= 4 and w.isalpha() and w.lower() not in {"also", "and", "add", "is", "accepted", "accept", "the", "as", "well", "to", "in", "or", "of", "be", "rule", "cart"}]
                    if new_codes:
                        existing_codes = last_rule.get("valid_values", [])
                        for nc in new_codes:
                            if nc not in existing_codes:
                                existing_codes.append(nc)
                        last_rule["valid_values"] = existing_codes
                        xslt = compile_bundle_to_xslt(session["cart"])
                        return {
                            "session_id": session_id,
                            "status": "ready",
                            "bot_message": f"Updated previous rule with new allowed values ({', '.join(existing_codes)}). Total rules in bundle: {len(session['cart'])}.",
                            "cart": session["cart"],
                            "compiled_xslt": xslt.strip(),
                            "quick_replies": []
                        }

            try:
                ir = self.parser.parse_rule(user_message)
            except Exception as e:
                return {"session_id": session_id, "status": "ready", "bot_message": f"Could not parse rule: {str(e)}. Please try rephrasing.", "cart": session["cart"], "quick_replies": []}
                
            session["draft_ir"] = ir
            
            # --- Verification Audit: Tax Categories ---
            if ir.get("rule_type") == "tax_category_validation":
                vals = ir.get("valid_values", [])
                std_codes = ["S", "E", "Z", "O", "K", "G", "AE"]
                unknowns = [v for v in vals if v not in std_codes]
                if unknowns:
                    session["status"] = "confirming_value"
                    u_str = ", ".join(unknowns)
                    q = [
                        {"label": f"Yes, add '{u_str}' as a valid custom category", "action": "add_value", "value": u_str},
                        {"label": "No, I meant 'E' (Exempt)", "action": "replace_value", "value": "E"},
                        {"label": "No, I meant 'S' (Standard)", "action": "replace_value", "value": "S"}
                    ]
                    return {
                        "session_id": session_id, 
                        "status": "confirming_value", 
                        "bot_message": f"I noticed '{u_str}' is not one of the standard e-invoicing tax categories (S, E, Z, O). How would you like to proceed?", 
                        "quick_replies": q, 
                        "draft_ir": ir, 
                        "cart": session["cart"]
                    }

            # If all audits pass, auto-add to cart and compile master bundle
            session["cart"].append(ir)
            session["draft_ir"] = None
            session["status"] = "ready"
            xslt = compile_bundle_to_xslt(session["cart"])
            return {
                "session_id": session_id, 
                "status": "ready", 
                "bot_message": f"Successfully parsed and added rule to Compliance Bundle! Total rules in bundle: {len(session['cart'])}.", 
                "cart": session["cart"], 
                "compiled_xslt": xslt.strip(), 
                "quick_replies": []
            }
            
        return {"session_id": session_id, "status": session.get("status", "ready"), "bot_message": "How can I assist you with invoice compliance?", "cart": session["cart"], "quick_replies": []}
