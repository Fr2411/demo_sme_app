"""Orchestrates specialized retail agents and optional OpenAI function-calling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .discount_supervisor import DiscountSupervisor
from .sales_agent import SalesAgent
from .stock_agent import StockAgent

try:
    from openai import OpenAI
except Exception:  # openai is optional at import time for local-only execution
    OpenAI = None


@dataclass
class AgentOrchestrator:
    model: str = "gpt-4o-mini"
    openai_client: Any = None

    def __post_init__(self) -> None:
        self.sales_agent = SalesAgent()
        self.stock_agent = StockAgent()
        self.discount_supervisor = DiscountSupervisor()

        if self.openai_client is None and OpenAI is not None:
            self.openai_client = OpenAI()

        # TypeScript-style function contract reference:
        # type AgentResult = { action: string; text: string; metadata?: Record<string, unknown> };
        self.function_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "sales_agent_decision",
                    "description": "Generate a sales-oriented recommendation with margin awareness.",
                    "parameters": self.sales_agent.input_schema,
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "stock_agent_decision",
                    "description": "Assess stock urgency and provide replenishment action.",
                    "parameters": self.stock_agent.input_schema,
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discount_supervisor_decision",
                    "description": "Apply discount approval policy and return approval action.",
                    "parameters": self.discount_supervisor.input_schema,
                },
            },
        ]

    def route(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return structured outputs from all agents for a single business event."""
        sales_out = self.sales_agent.evaluate(payload)
        stock_out = self.stock_agent.evaluate(payload)
        discount_out = self.discount_supervisor.evaluate(payload)
        return {
            "action": "orchestrated_plan",
            "text": "Combined guidance from sales, stock, and discount supervisors.",
            "metadata": {
                "sales_agent": sales_out,
                "stock_agent": stock_out,
                "discount_supervisor": discount_out,
            },
        }

    def call_openai_with_functions(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Use OpenAI function-calling to request the best tool call for the payload."""
        if self.openai_client is None:
            return {
                "action": "local_fallback",
                "text": "OpenAI client unavailable; returning local orchestration.",
                "metadata": self.route(payload),
            }

        user_prompt = (
            "Decide which function to call for this retail request and return compliant args:\n"
            + json.dumps(payload)
        )
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a retail AI orchestrator. Use function tools for decisions and "
                        "respect sales push, margin safety, stock urgency, and discount approvals."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            tools=self.function_schemas,
            tool_choice="auto",
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            return {
                "action": "no_tool_call",
                "text": msg.content or "Model responded without tool usage.",
            }

        tool_call = msg.tool_calls[0]
        return {
            "action": "tool_call_selected",
            "text": f"Model selected {tool_call.function.name}",
            "metadata": {
                "function": tool_call.function.name,
                "arguments": json.loads(tool_call.function.arguments or "{}"),
            },
        }
