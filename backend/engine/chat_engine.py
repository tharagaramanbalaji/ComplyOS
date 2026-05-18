"""
ChatEngine – conversational rule builder.

Key invariant: confirmation tokens (yes / no / proceed / cancel) NEVER
become part of the rule text.  All state transitions go through the
ConversationSession state machine.
"""
import re
import difflib
from typing import Dict, Optional

from schemas.schema import ChatContext, ChatResponse
from engine.conversation_state import ConversationSession, is_control_token, State


class ChatEngine:
    def __init__(self):
        self.allowed_values = {
            "tax_categories": ["S", "E", "Z", "O", "K", "L", "M", "AE", "SE"],
            "currency_codes": ["AED", "USD", "EUR", "GBP", "INR"],
        }

        # session_id → ConversationSession (richer object)
        self._sessions: Dict[str, ConversationSession] = {}
        # session_id → ChatContext  (Pydantic response model)
        self._contexts: Dict[str, ChatContext] = {}

    # ── session management ────────────────────────────────────────────────

    def get_or_create_session(self, session_id: str) -> ChatContext:
        if session_id not in self._contexts:
            self._contexts[session_id] = ChatContext(conversation_id=session_id)
            self._sessions[session_id] = ConversationSession(session_id)
        return self._contexts[session_id]

    def _session(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self.get_or_create_session(session_id)
        return self._sessions[session_id]

    # ── main message handler ──────────────────────────────────────────────

    def process_message(
        self,
        session_id: str,
        text: str,
        is_clarification_response: bool = False,
        clarification_type: Optional[str] = None,
    ) -> ChatResponse:
        sess = self._session(session_id)
        stripped = text.strip()

        # ── GATE: strip pure control tokens before any processing ─────────
        if is_control_token(stripped):
            return self._handle_control(sess, stripped)

        # ── clarification response ────────────────────────────────────────
        if is_clarification_response or sess.state == State.WAITING_CLARIFICATION:
            return self._handle_clarification(sess, stripped, clarification_type)

        # ── normal rule input ─────────────────────────────────────────────
        return self._handle_rule_input(sess, stripped)

    # ── control token handler (yes / no / proceed / cancel / continue) ───

    def _handle_control(self, sess: ConversationSession, token: str) -> ChatResponse:
        t = token.lower()
        if t in ("yes", "y", "proceed", "continue", "ok", "okay"):
            if sess.state == State.WAITING_CONFIRMATION:
                sess.confirm()
                return ChatResponse(
                    message="Rule confirmed. Generating IR…",
                    status="resolved",
                    finalized_rule=sess.finalized_rule,
                    confidence_score=1.0,
                )
            elif sess.state == State.BUILDING_RULE:
                # User said yes while building – treat as "finalize now"
                sess.confirm()
                return ChatResponse(
                    message="Rule finalized.",
                    status="resolved",
                    finalized_rule=sess.finalized_rule,
                    confidence_score=1.0,
                )
            else:
                return ChatResponse(
                    message="No active rule to confirm. Please describe a rule first.",
                    status="active",
                )

        if t in ("no", "n", "cancel"):
            sess.cancel()
            return ChatResponse(
                message="Cancelled. You can start describing a new rule.",
                status="active",
            )

        return ChatResponse(message="I didn't understand that.", status="active")

    # ── clarification handler ─────────────────────────────────────────────

    def _handle_clarification(
        self,
        sess: ConversationSession,
        text: str,
        clarification_type: Optional[str],
    ) -> ChatResponse:
        q = sess.pending_question or {}
        q_type = clarification_type or q.get("type", "")

        if q_type == "tax_category":
            # User either confirmed an alternate category or typed a new one
            cat_match = re.search(r'\b([A-Z]{1,2}[0-9]?)\b', text.upper())
            cat = cat_match.group(1) if cat_match else text.strip().upper()
            # Merge back into rule
            merged_rule = sess.get_merged_rule() + f" {cat}"
            sess.rule_parts[-1] = sess.rule_parts[-1] + f" {cat}"
            sess.state = State.WAITING_CONFIRMATION
            return ChatResponse(
                message=f"Got it – tax category is '{cat}'. Shall I finalize the rule?",
                options=["yes", "no"],
                status="clarification_required",
                clarification_type=None,
                confidence_score=0.9,
            )

        if q_type == "high_threshold":
            num = re.search(r'\d+', text)
            if num:
                threshold = num.group(0)
                # Replace "high" placeholder in the last rule fragment
                if sess.rule_parts:
                    sess.rule_parts[-1] = re.sub(
                        r'\bhigh\b', f"> {threshold}", sess.rule_parts[-1], flags=re.IGNORECASE
                    )
                sess.pending_question = None
                sess.state = State.BUILDING_RULE
                return ChatResponse(
                    message=f"Threshold set to {threshold}. Anything else to add?",
                    status="active",
                    confidence_score=0.9,
                )

        # Generic fallback – just fold the answer in and continue
        sess.state = State.BUILDING_RULE
        sess.pending_question = None
        return ChatResponse(
            message="Understood. Anything else?",
            status="active",
        )

    # ── rule input handler ────────────────────────────────────────────────

    def _handle_rule_input(
        self, sess: ConversationSession, text: str
    ) -> ChatResponse:
        text_lower = text.lower()

        # 1. Ambiguity – "amount high"
        if re.search(r'\b(?:amount|tax|value)\b.*\bhigh\b', text_lower):
            sess.add_rule_fragment(text)
            sess.await_clarification({"type": "high_threshold"})
            return ChatResponse(
                message="Can you clarify 'high'? What is the threshold?",
                options=["greater than 100", "greater than 1000", "custom value"],
                status="clarification_required",
                clarification_type="high_threshold",
                confidence_score=0.5,
            )

        # 2. Tax category validation check
        cat_match = re.search(
            r'\btax.?categor(?:y|ies)\b.*\b(?:should be|must be|is|=)\s+([A-Za-z0-9]+)',
            text_lower,
        )
        if cat_match:
            cat = cat_match.group(1).upper()
            if cat not in self.allowed_values["tax_categories"]:
                close = difflib.get_close_matches(
                    cat, self.allowed_values["tax_categories"], n=2, cutoff=0.3
                )
                options = [f"Did you mean {m}?" for m in close]
                options.append(f"Add {cat} as a valid category")
                sess.add_rule_fragment(text)
                sess.await_clarification({"type": "tax_category", "value": cat})
                return ChatResponse(
                    message=f"'{cat}' is not a known tax category. Did you mean one of these?",
                    options=options,
                    status="clarification_required",
                    clarification_type="tax_category",
                    confidence_score=0.4,
                )

        # 3. Normal rule fragment
        sess.add_rule_fragment(text)

        # 4. Decide whether to finalize immediately or ask for more
        is_complete = self._looks_complete(text_lower)

        if is_complete:
            # Ask for confirmation (don't finalize yet)
            sess.await_confirmation()
            return ChatResponse(
                message=(
                    f"Understood: '{text}'.\n"
                    "Proceed with this rule? (yes / no)"
                ),
                options=["yes", "no"],
                status="clarification_required",
                clarification_type="confirmation",
                confidence_score=0.95,
            )
        else:
            # Incomplete – ask if there's a continuation
            # If we already have > 1 fragment, merge and finalize
            if len(sess.rule_parts) > 1:
                merged = sess.get_merged_rule()
                if "if " not in merged.lower():
                    merged = "If " + merged
                sess.finalized_rule = merged
                sess.state = State.FINALIZED
                return ChatResponse(
                    message=f"Merged rule: '{merged}'. Finalizing.",
                    status="resolved",
                    finalized_rule=merged,
                    confidence_score=0.9,
                )
            return ChatResponse(
                message="Condition understood. Anything else to add?",
                status="active",
                confidence_score=0.7,
            )

    def _looks_complete(self, text: str) -> bool:
        """Heuristic: does this single sentence look like a complete rule?"""
        complete_signals = [
            r'\brequired\b',
            r'\bunique\b',
            r'\b(?:future|current date|current_date|today)\b',
            r'\bpositive\b',
            r'[><=]\s*\d+',
            r'\bif\b.*[><=].*\brequired\b',
            r'\bwhenever\b',
        ]
        for sig in complete_signals:
            if re.search(sig, text, re.IGNORECASE):
                return True
        return False

    def resolve_conversation(self, session_id: str) -> str:
        sess = self._session(session_id)
        merged = sess.get_merged_rule()
        if len(sess.rule_parts) > 1 and "if " not in merged.lower():
            merged = "If " + merged
        sess.finalized_rule = merged
        sess.state = State.FINALIZED
        return merged
