"""Stock agent for inventory urgency and replenishment actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .prompt_utils import build_agent_context


@dataclass
class StockAgent:
    name: str = "stock_agent"

    # TypeScript-style schema mirror:
    # type StockInput = {
    #   product_name: string;
    #   stock_days_cover: number;
    #   reorder_lead_days: number;
    #   daily_sales_velocity: number;
    # }
    input_schema: dict[str, Any] = None

    def __post_init__(self) -> None:
        self.input_schema = {
            "type": "object",
            "required": ["product_name", "stock_days_cover", "reorder_lead_days", "daily_sales_velocity"],
            "properties": {
                "product_name": {"type": "string"},
                "stock_days_cover": {"type": "number"},
                "reorder_lead_days": {"type": "number"},
                "daily_sales_velocity": {"type": "number"},
            },
            "additionalProperties": False,
        }

    def build_prompt(self, payload: dict[str, Any]) -> str:
        return build_agent_context(self.name, payload)

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        stock_cover = payload["stock_days_cover"]
        lead = payload["reorder_lead_days"]
        if stock_cover <= 3:
            action = "expedite_reorder"
            text = f"Critical low stock for {payload['product_name']}; expedite reorder immediately."
            urgency = "HIGH"
        elif stock_cover <= 7 or stock_cover <= lead:
            action = "schedule_reorder"
            text = f"Reorder {payload['product_name']} this cycle to prevent stockout risk."
            urgency = "MEDIUM"
        else:
            action = "monitor_stock"
            text = f"Stock for {payload['product_name']} is stable; continue routine monitoring."
            urgency = "LOW"
        return {"action": action, "text": text, "metadata": {"urgency": urgency, "stock_days_cover": stock_cover}}
