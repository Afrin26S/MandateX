"""
The Commerce Mandate for TechBazaar.

This is the whole point of the project: these rules are data, not prompt
text, and every financial action gets checked against them in mandate_engine.py
— never inside the LLM. Change the numbers here, nothing else.
"""

MANDATE = {
    "merchant": "TechBazaar",
    "max_per_order": 3000,
    "max_per_day": 10000,
    "confirmation_required_above": 2000,
    "allowed_categories": ["electronics-accessories"],
    "allowed_actions": ["search_catalog", "view_price", "create_order"],
    "forbidden_actions": ["refund", "payout", "change_price", "change_bank_details", "delete_order"],
}