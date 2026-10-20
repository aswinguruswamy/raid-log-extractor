"""Cost of one run (story S1-09, KAN-14).

Prices in US dollars per million tokens (input, output), from
https://platform.claude.com/docs/en/models/overview on 2026-10-20.
Check that page when prices change.
"""

from __future__ import annotations

from typing import Optional

PRICES_PER_MTOK = {
    "claude-fable-5-1": (10.00, 50.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),  # the page shows "from" prices for Haiku
}

COST_TARGET_USD = 0.10  # charter target for a 1-hour transcript


def run_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """Cost of one run in US dollars, or None when the model price is unknown."""
    prices = PRICES_PER_MTOK.get(model)
    if prices is None:
        return None
    input_price, output_price = prices
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def format_run(model: str, input_tokens: int, output_tokens: int, seconds: float) -> str:
    """One line for the terminal: tokens, cost, and time."""
    cost = run_cost(model, input_tokens, output_tokens)
    cost_text = f"${cost:.4f}" if cost is not None else "unknown (no price for this model)"
    return (
        f"Model: {model} | Tokens: {input_tokens:,} in / {output_tokens:,} out | "
        f"Cost: {cost_text} | Time: {seconds:.1f} s"
    )
