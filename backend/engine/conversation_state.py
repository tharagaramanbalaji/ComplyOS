from enum import Enum
from typing import Optional


class State(str, Enum):
    IDLE = "IDLE"
    BUILDING_RULE = "BUILDING_RULE"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    WAITING_CLARIFICATION = "WAITING_CLARIFICATION"
    FINALIZED = "FINALIZED"


# Tokens that are NEVER part of rule text
_CONFIRMATION_TOKENS = {"yes", "y", "no", "n", "proceed", "continue", "cancel", "ok", "okay"}


def is_control_token(text: str) -> bool:
    """Return True if the text is a confirmation/cancel command, not rule content."""
    return text.strip().lower() in _CONFIRMATION_TOKENS


class ConversationSession:
    """
    Tracks a single user conversation.

    Key guarantee: confirmation / cancel replies NEVER touch `rule_parts`.
    They only advance or reset the state machine.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state: State = State.IDLE
        self.rule_parts: list[str] = []          # actual rule fragments
        self.pending_question: Optional[dict] = None  # {type, payload}
        self.finalized_rule: Optional[str] = None
        self.selected_values: dict = {}

    # ── state transitions ─────────────────────────────────────────────────

    def add_rule_fragment(self, text: str) -> None:
        """Append a genuine rule fragment (never a confirmation token)."""
        self.rule_parts.append(text)
        self.state = State.BUILDING_RULE

    def await_confirmation(self) -> None:
        self.state = State.WAITING_CONFIRMATION

    def await_clarification(self, question: dict) -> None:
        self.pending_question = question
        self.state = State.WAITING_CLARIFICATION

    def confirm(self) -> None:
        """User said yes/proceed → finalize."""
        self.finalized_rule = " ".join(self.rule_parts)
        self.state = State.FINALIZED

    def cancel(self) -> None:
        """User said no/cancel → reset."""
        self.rule_parts = []
        self.pending_question = None
        self.finalized_rule = None
        self.state = State.IDLE

    def get_merged_rule(self) -> str:
        return " ".join(self.rule_parts)

    def is_confirmed(self) -> bool:
        return self.state == State.FINALIZED

    def is_awaiting(self) -> bool:
        return self.state in (State.WAITING_CONFIRMATION, State.WAITING_CLARIFICATION)
