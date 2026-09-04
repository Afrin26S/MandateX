"""
The Mandate Engine.

This is the piece that matters most in the whole project. It is the ONLY
place financial decisions get made. The LLM agent never gets to decide
whether an action is allowed — it can only ask, and this module answers.

Design rule: every function here takes plain data in, returns a plain
decision out. No LLM calls, no prompts, nothing non-deterministic. That's
what makes it auditable and testable.
"""

from dataclasses import dataclass
from .mandate_config import MANDATE
from .catalog import find_product


@dataclass
class Decision:
    allowed: bool
    reason: str
    needs_confirmation: bool = False


class MandateEngine:
    def __init__(self, mandate: dict = MANDATE):
        self.mandate = mandate
        self.spent_today = 0  # in a real system this is per-user, persisted; fine as in-memory for a demo

    def check_action(self, action: str) -> Decision:
        """Step 0 for every request: is this action even in the allowed set?"""
        if action in self.mandate["forbidden_actions"]:
            return Decision(False, f"Action '{action}' is explicitly forbidden by this mandate.")
        if action not in self.mandate["allowed_actions"]:
            return Decision(False, f"Action '{action}' is not in the allowed action list.")
        return Decision(True, "Action permitted.")

    def check_purchase(self, product_id: str, quantity: int = 1) -> Decision:
        """The core check for a create_order action."""
        action_decision = self.check_action("create_order")
        if not action_decision.allowed:
            return action_decision

        product = find_product(product_id)
        if product is None:
            return Decision(False, f"Product '{product_id}' does not exist in the catalog.")

        if product["category"] not in self.mandate["allowed_categories"]:
            return Decision(
                False,
                f"Category '{product['category']}' is not covered by this mandate "
                f"(allowed: {self.mandate['allowed_categories']}).",
            )

        total = product["price"] * quantity

        if total > self.mandate["max_per_order"]:
            return Decision(
                False,
                f"Order total \u20b9{total} exceeds per-order limit of \u20b9{self.mandate['max_per_order']}.",
            )

        if self.spent_today + total > self.mandate["max_per_day"]:
            return Decision(
                False,
                f"Order would push today's spend to \u20b9{self.spent_today + total}, "
                f"exceeding daily limit of \u20b9{self.mandate['max_per_day']}.",
            )

        needs_confirmation = total > self.mandate["confirmation_required_above"]
        return Decision(
            True,
            f"Order of \u20b9{total} approved" + (" (user confirmation required)." if needs_confirmation else "."),
            needs_confirmation=needs_confirmation,
        )

    def record_spend(self, amount: int):
        """Call this only after a payment actually succeeds."""
        self.spent_today += amount