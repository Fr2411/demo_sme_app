"""Sales agent focused on conversion-safe recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .prompt_utils import build_agent_context


@dataclass
class SalesAgent:
    name: str = "sales_agent"

    # TypeScript-style schema mirror:
    # type SalesInput = {
    #   product_name: string;
    #   stock_days_cover: number;
    #   current_margin_pct: number;
    #   requested_discount_pct: number;
    #   campaign_goal?: string;
    # }
    input_schema: dict[str, Any] = None  # assigned in __post_init__

    def __post_init__(self) -> None:
        self.input_schema = {
            "type": "object",
            "required": [
                "product_name",
                "stock_days_cover",
                "current_margin_pct",
                "requested_discount_pct",
            ],
            "properties": {
                "product_name": {"type": "string"},
                "stock_days_cover": {"type": "number"},
                "current_margin_pct": {"type": "number"},
                "requested_discount_pct": {"type": "number"},
                "campaign_goal": {"type": "string"},
            },
            "additionalProperties": False,
        }

    def build_prompt(self, payload: dict[str, Any]) -> str:
        return build_agent_context(self.name, payload)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        margin_after_discount = payload["current_margin_pct"] - payload["requested_discount_pct"]
        if margin_after_discount < 20:
            action = "upsell_instead_of_discount"
            text = (
                f"Avoid discounting {payload['product_name']}; margin falls to "
                f"{margin_after_discount:.1f}%. Recommend value-add upsell."
            )
        elif payload["stock_days_cover"] <= 3:
            action = "push_sales_with_urgency"
            text = (
                f"Run urgency messaging for {payload['product_name']} and approve a "
                f"{payload['requested_discount_pct']:.1f}% promo."
            )
        else:
            action = "standard_sales_push"
            text = (
                f"Promote {payload['product_name']} with benefit-led messaging; "
                "no aggressive urgency needed."
            )
        return {"action": action, "text": text, "metadata": {"margin_after_discount": margin_after_discount}}
