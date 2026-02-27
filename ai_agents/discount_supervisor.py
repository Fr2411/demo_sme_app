"""Discount supervisor agent to enforce margin and approval policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .prompt_utils import build_agent_context


@dataclass
class DiscountSupervisor:
    name: str = "discount_supervisor"

    # TypeScript-style schema mirror:
    # type DiscountInput = {
    #   product_name: string;
    #   current_margin_pct: number;
    #   requested_discount_pct: number;
    #   minimum_margin_pct?: number;
    #   strategic_override?: boolean;
    # }
    input_schema: dict[str, Any] = None

    def __post_init__(self) -> None:
        self.input_schema = {
            "type": "object",
            "required": ["product_name", "current_margin_pct", "requested_discount_pct"],
            "properties": {
                "product_name": {"type": "string"},
                "current_margin_pct": {"type": "number"},
                "requested_discount_pct": {"type": "number"},
                "minimum_margin_pct": {"type": "number", "default": 20},
                "strategic_override": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        }

    def build_prompt(self, payload: dict[str, Any]) -> str:
        return build_agent_context(self.name, payload)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        floor = payload.get("minimum_margin_pct", 20)
        post_discount_margin = payload["current_margin_pct"] - payload["requested_discount_pct"]
        override = payload.get("strategic_override", False)
        requested = payload["requested_discount_pct"]

        if post_discount_margin < floor and not override:
            action = "reject_discount"
            text = (
                f"Reject {requested:.1f}% discount for {payload['product_name']}: "
                f"margin drops to {post_discount_margin:.1f}% below floor {floor:.1f}%."
            )
        elif requested > 20 or (post_discount_margin < floor and override):
            action = "executive_approval_required"
            text = "Escalate to executive approver due to high discount risk."
        elif requested > 10:
            action = "supervisor_review_required"
            text = "Request supervisor review before publishing this discount."
        else:
            action = "approve_discount"
            text = "Discount approved automatically under policy."

        return {
            "action": action,
            "text": text,
            "metadata": {
                "post_discount_margin": post_discount_margin,
                "minimum_margin_pct": floor,
            },
        }
