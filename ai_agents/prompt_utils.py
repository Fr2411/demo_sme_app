"""Prompt utilities for multi-agent retail decisioning."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def sales_push_rules() -> str:
    return (
        "Sales Push Rules:\n"
        "1. Prioritize products with healthy stock (>= 14 days cover).\n"
        "2. Favor SKUs with high conversion potential and low return rate.\n"
        "3. Use urgency language only when inventory is genuinely constrained."
    )


def margin_rules() -> str:
    return (
        "Margin Rules:\n"
        "1. Protect target gross margin floor (default 20%).\n"
        "2. Never recommend discounts that push below the floor unless an explicit override exists.\n"
        "3. If margin floor is violated, propose alternatives (bundle, upsell, smaller discount)."
    )


def stock_urgency_rules() -> str:
    return (
        "Stock Urgency Rules:\n"
        "1. Mark HIGH urgency for <= 3 days of cover.\n"
        "2. Mark MEDIUM urgency for <= 7 days of cover.\n"
        "3. Mark LOW urgency above 7 days and avoid panic messaging."
    )


def discount_approval_rules() -> str:
    return (
        "Discount Approval Rules:\n"
        "1. Auto-approve discounts <= 10% when margin floor remains safe.\n"
        "2. Require supervisor review for 10-20% discounts.\n"
        "3. Escalate >20% discounts or any margin-floor violation for final approval."
    )


def build_agent_context(agent_name: str, payload: dict[str, Any]) -> str:
    """Return a normalized business-context prompt block."""
    sections = [
        f"Agent: {agent_name}",
        sales_push_rules(),
        margin_rules(),
        stock_urgency_rules(),
        discount_approval_rules(),
        "Structured Input:\n" + _json_block(payload),
        (
            "Response Contract:\n"
            "Return strict JSON with keys: action (string), text (string), and optional metadata (object)."
        ),
    ]
    return "\n\n".join(sections)
