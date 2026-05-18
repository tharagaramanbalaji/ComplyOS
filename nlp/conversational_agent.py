from nlp.parser import NLPRuleParser
from engine.compiler.xslt_generator import compile_bundle_to_xslt, compile_rule_to_xslt
import re

# Global in-memory session store for multi-turn state retention
SESSION_STORE = {}

# Maps rule_type to a human-readable label for display in deletion messages
RULE_TYPE_LABELS = {
    "required_field": "required field",
    "conditional_required_field": "conditional required field",
    "numeric_comparison": "numeric comparison",
    "amount_calculation": "amount calculation",
    "currency_consistency": "currency consistency",
    "tax_category_validation": "tax category",
    "date_validation": "date validation",
    "duplicate_field_check": "duplicate check",
}

# Keyword groups for deletion intent detection
DELETE_KEYWORDS = {"remove", "delete", "drop", "clear", "erase", "undo", "take out"}

# Keyword groups to identify which rule to delete by type
RULE_TYPE_KEYWORDS = {
    "required_field": {"required", "mandatory", "present", "exists", "field"},
    "numeric_comparison": {"amount", "numeric", "number", "value", "greater", "less", "minimum", "maximum"},
    "amount_calculation": {"calculation", "sum", "total", "payable", "equation", "equals"},
    "currency_consistency": {"currency", "eur", "usd", "gbp", "consistent"},
    "tax_category_validation": {"tax", "category", "vat", "code"},
    "date_validation": {"date", "due", "issued", "today", "timestamp"},
    "duplicate_field_check": {"duplicate", "unique", "resubmission"},
}

# Candidate fields to offer as clarification options
FIELD_OPTIONS = {
    "numeric_comparison": [
        {"label": "Payable Amount (final total)", "action": "set_field", "value": "payable_amount"},
        {"label": "Taxable Amount (before tax)", "action": "set_field", "value": "taxable_amount"},
        {"label": "Tax Amount (VAT)", "action": "set_field", "value": "tax_amount"},
        {"label": "Line Item Amount", "action": "set_field", "value": "line_items[*].amount"},
    ],
    "date_validation": [
        {"label": "Issue Date (when invoice was created)", "action": "set_field", "value": "issue_date"},
        {"label": "Due Date (payment deadline)", "action": "set_field", "value": "due_date"},
    ],
    "required_field": [
        {"label": "Invoice ID", "action": "set_field", "value": "invoice_id"},
        {"label": "Seller Name", "action": "set_field", "value": "seller_name"},
        {"label": "Buyer Name", "action": "set_field", "value": "buyer_name"},
        {"label": "Tax Amount", "action": "set_field", "value": "tax_amount"},
        {"label": "Issue Date", "action": "set_field", "value": "issue_date"},
        {"label": "Tax Exemption Reason", "action": "set_field", "value": "tax_exemption_reason"},
    ],
}

# Confidence threshold below which we ask for clarification
CONFIDENCE_THRESHOLD = 0.60


def _detect_delete_intent(lower_msg: str) -> bool:
    """Returns True if the message is a deletion command."""
    return any(kw in lower_msg for kw in DELETE_KEYWORDS)


def _resolve_delete_target(lower_msg: str, cart: list):
    """
    Parses a deletion command and returns the (index, rule) to remove, or None.
    Supports:
      - By number:   "remove rule 2", "delete 1"
      - By type kw:  "delete the currency rule", "remove tax category"
      - Last rule:   "undo last rule", "remove last"
    """
    # By rule number
    m = re.search(r'\b(\d+)\b', lower_msg)
    if m:
        idx = int(m.group(1)) - 1  # 1-indexed → 0-indexed
        if 0 <= idx < len(cart):
            return idx

    # "last" keyword
    if "last" in lower_msg and cart:
        return len(cart) - 1

    # By rule type keyword match
    for rule_type, keywords in RULE_TYPE_KEYWORDS.items():
        if any(kw in lower_msg for kw in keywords):
            for idx, rule in enumerate(cart):
                if rule.get("rule_type") == rule_type:
                    return idx

    return None


def _needs_field_clarification(ir: dict) -> bool:
    """
    Returns True when the NLP parsed a low-confidence field mapping for
    rule types that benefit from explicit confirmation.
    """
    clarifiable_types = {"numeric_comparison", "date_validation", "required_field"}
    if ir.get("rule_type") not in clarifiable_types:
        return False
    confidence = ir.get("_field_confidence", 1.0)
    return confidence < CONFIDENCE_THRESHOLD


def _build_clarification_response(session_id: str, ir: dict, session: dict) -> dict:
    """Builds the quick-reply clarification response for ambiguous field mapping."""
    rule_type = ir.get("rule_type")
    guessed_field = ir.get("field", "unknown")
    options = FIELD_OPTIONS.get(rule_type, [])

    guessed_label = guessed_field.replace("_", " ").replace("line_items[*].", "line item ")
    msg = (
        f"I detected a **{RULE_TYPE_LABELS.get(rule_type, rule_type)}** rule, "
        f"but I'm not confident which field you meant (my best guess was `{guessed_label}`). "
        f"Which field should this rule apply to?"
    )

    return {
        "session_id": session_id,
        "status": "confirming_field",
        "bot_message": msg,
        "quick_replies": options,
        "draft_ir": ir,
        "cart": session["cart"],
    }


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

        # ── Explicit cart actions ──────────────────────────────────────────────
        if action == "clear_cart":
            session["cart"] = []
            session["status"] = "ready"
            session["draft_ir"] = None
            return {"session_id": session_id, "status": "ready",
                    "bot_message": "Compliance bundle cleared. You can start building a new rule bundle.",
                    "cart": [], "quick_replies": []}

        if action == "compile_cart":
            if not session["cart"]:
                return {"session_id": session_id, "status": "ready",
                        "bot_message": "Your compliance bundle is currently empty.",
                        "cart": [], "quick_replies": []}
            xslt = compile_bundle_to_xslt(session["cart"])
            session["status"] = "ready"
            return {
                "session_id": session_id, "status": "ready",
                "bot_message": f"Successfully compiled {len(session['cart'])} rules into a unified Master Compliance Bundle!",
                "cart": session["cart"], "compiled_xslt": xslt.strip(), "quick_replies": []
            }

        # ── Quick-reply interactive choices ───────────────────────────────────
        if user_choice:
            draft = session.get("draft_ir")
            if draft:
                act = user_choice.get("action")
                val = user_choice.get("value")

                if act == "add_value":
                    if "valid_values" not in draft:
                        draft["valid_values"] = ["S", "E", "Z", "O"]
                    if val not in draft["valid_values"]:
                        draft["valid_values"].append(val)
                elif act == "replace_value":
                    draft["valid_values"] = [val]
                elif act == "set_field":
                    # Feature 2: user confirmed the correct field
                    draft["field"] = val
                    draft.pop("_field_confidence", None)  # clean internal key

                # Upsert into cart
                existing_idx = next(
                    (i for i, r in enumerate(session["cart"])
                     if r.get("rule_type") == draft.get("rule_type") and r.get("field") == draft.get("field")),
                    -1
                )
                if existing_idx != -1:
                    session["cart"][existing_idx] = draft
                    msg = f"Updated existing rule for '{draft.get('field')}' in your Compliance Bundle! Total rules in bundle: {len(session['cart'])}."
                else:
                    session["cart"].append(draft)
                    msg = f"Rule confirmed and added to your Compliance Bundle! Total rules in bundle: {len(session['cart'])}."

                session["draft_ir"] = None
                session["status"] = "ready"
                xslt = compile_bundle_to_xslt(session["cart"])
                return {
                    "session_id": session_id, "status": "ready", "bot_message": msg,
                    "cart": session["cart"], "compiled_xslt": xslt.strip(), "quick_replies": []
                }

        # ── Natural language messages ──────────────────────────────────────────
        if user_message:
            session["history"].append({"role": "user", "content": user_message})
            lower_msg = user_message.lower().strip()

            # ── FEATURE 1: Natural language rule deletion ──────────────────────
            if _detect_delete_intent(lower_msg):
                cart = session["cart"]
                if not cart:
                    return {
                        "session_id": session_id, "status": "ready",
                        "bot_message": "Your compliance bundle is already empty — nothing to remove.",
                        "cart": [], "quick_replies": []
                    }

                idx = _resolve_delete_target(lower_msg, cart)
                if idx is not None:
                    removed = cart.pop(idx)
                    rule_label = RULE_TYPE_LABELS.get(removed.get("rule_type"), removed.get("rule_type", "rule"))
                    field_label = removed.get("field", "").replace("_", " ")
                    xslt = compile_bundle_to_xslt(cart) if cart else None
                    resp = {
                        "session_id": session_id, "status": "ready",
                        "bot_message": f"🗑️ Removed the **{rule_label}** rule for `{field_label}` from your bundle. "
                                       f"Remaining rules: {len(cart)}.",
                        "cart": cart, "quick_replies": []
                    }
                    if xslt:
                        resp["compiled_xslt"] = xslt.strip()
                    return resp
                else:
                    # Could not identify which rule to delete — list available rules
                    rule_list = "\n".join(
                        f"  Rule {i+1}: {RULE_TYPE_LABELS.get(r.get('rule_type'), r.get('rule_type'))} on `{r.get('field', '?')}`"
                        for i, r in enumerate(cart)
                    )
                    return {
                        "session_id": session_id, "status": "ready",
                        "bot_message": (
                            "I couldn't identify which rule to remove. "
                            "Try saying *'remove rule 2'* or *'delete the currency rule'*.\n\n"
                            f"Your current rules:\n{rule_list}"
                        ),
                        "cart": cart, "quick_replies": []
                    }

            # ── Multi-Turn Rule Continuation Logic ────────────────────────────
            is_continuation = any(lower_msg.startswith(w) or f" {w} " in f" {lower_msg} "
                                  for w in ["also", "and", "add", "include", "accept", "accepted"])
            if session["cart"] and is_continuation:
                last_rule = session["cart"][-1]
                if last_rule.get("rule_type") == "tax_category_validation":
                    clean_words = [w.strip(".'\",:;!?()[]{}") for w in user_message.split()]
                    new_codes = [w.upper() for w in clean_words
                                 if len(w) <= 4 and w.isalpha()
                                 and w.lower() not in {"also", "and", "add", "is", "accepted", "accept",
                                                       "the", "as", "well", "to", "in", "or", "of", "be",
                                                       "rule", "cart"}]
                    if new_codes:
                        existing_codes = last_rule.get("valid_values", [])
                        for nc in new_codes:
                            if nc not in existing_codes:
                                existing_codes.append(nc)
                        last_rule["valid_values"] = existing_codes
                        xslt = compile_bundle_to_xslt(session["cart"])
                        return {
                            "session_id": session_id, "status": "ready",
                            "bot_message": f"Updated previous rule with new allowed values ({', '.join(existing_codes)}). "
                                           f"Total rules in bundle: {len(session['cart'])}.",
                            "cart": session["cart"], "compiled_xslt": xslt.strip(), "quick_replies": []
                        }

            # ── Parse new rule ─────────────────────────────────────────────────
            try:
                ir = self.parser.parse_rule(user_message)
            except Exception as e:
                return {"session_id": session_id, "status": "ready",
                        "bot_message": f"Could not parse rule: {str(e)}. Please try rephrasing.",
                        "cart": session["cart"], "quick_replies": []}

            session["draft_ir"] = ir

            # ── FEATURE 2a: Clarification audit for ambiguous field mapping ────
            if _needs_field_clarification(ir):
                session["status"] = "confirming_field"
                return _build_clarification_response(session_id, ir, session)

            # ── FEATURE 2b: Existing tax-category audit ────────────────────────
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
                        {"label": "No, I meant 'S' (Standard)", "action": "replace_value", "value": "S"},
                    ]
                    return {
                        "session_id": session_id, "status": "confirming_value",
                        "bot_message": f"I noticed '{u_str}' is not one of the standard e-invoicing tax categories (S, E, Z, O). How would you like to proceed?",
                        "quick_replies": q, "draft_ir": ir, "cart": session["cart"]
                    }

            # ── Upsert rule into cart ──────────────────────────────────────────
            existing_idx = next(
                (i for i, r in enumerate(session["cart"])
                 if r.get("rule_type") == ir.get("rule_type") and r.get("field") == ir.get("field")),
                -1
            )

            if existing_idx != -1:
                if session["cart"][existing_idx] == ir:
                    msg = f"⚠️ This rule is already active in your Compliance Bundle! (Total rules: {len(session['cart'])})"
                else:
                    session["cart"][existing_idx] = ir
                    msg = f"🔄 Updated existing rule for '{ir.get('field', 'invoice')}' in your Compliance Bundle! Total rules: {len(session['cart'])}."
            else:
                session["cart"].append(ir)
                msg = f"✅ Successfully parsed and added rule to Compliance Bundle! Total rules in bundle: {len(session['cart'])}."

            session["draft_ir"] = None
            session["status"] = "ready"
            xslt = compile_bundle_to_xslt(session["cart"])
            return {
                "session_id": session_id, "status": "ready", "bot_message": msg,
                "cart": session["cart"], "compiled_xslt": xslt.strip(), "quick_replies": []
            }

        return {"session_id": session_id, "status": session.get("status", "ready"),
                "bot_message": "How can I assist you with invoice compliance?",
                "cart": session["cart"], "quick_replies": []}
