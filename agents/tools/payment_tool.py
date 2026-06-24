"""
Payment Tool — Stripe Integration

LangChain StructuredTool to charge a client or issue a refund via Stripe API.
Called by the ACT node when tool_name = "payment_action"
"""
import os
from typing import Any, Dict, Optional, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class PaymentInput(BaseModel):
    tenant_id:   str                          = Field(..., description="Tenant ID context")
    action:      Literal["charge", "refund"] = Field(..., description="Stripe action to execute")
    amount:      float                        = Field(..., description="Amount in currency units (e.g. 50.00)")
    currency:    str                          = Field(default="USD", description="Currency code (USD, INR, EUR)")
    customer_id: str                          = Field(..., description="Stripe Customer ID or email")
    payment_method_id: Optional[str]          = Field(default=None, description="Stripe payment method token (required for charges)")
    invoice_id:  Optional[str]                = Field(default=None, description="Invoice reference ID")


@tool(args_schema=PaymentInput)
async def payment_tool(
    tenant_id: str,
    action: Literal["charge", "refund"],
    amount: float,
    currency: str,
    customer_id: str,
    payment_method_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Initiate customer billing or refunds on Stripe.
    """
    print(f"  💳 [payment_tool] action={action} | amount={currency} {amount} | customer={customer_id}")

    # TODO: Replace with stripe-python SDK:
    # import stripe; stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    # if action == "charge":
    #   intent = stripe.PaymentIntent.create(...)
    # elif action == "refund":
    #   refund = stripe.Refund.create(...)

    # ── Stub response ─────────────────────────────────────────────────────
    tx_id = "ch_3M4k92LkdIwHu7ix1a8d0f7a"
    return {
        "status":        "success",
        "action":        action,
        "transaction_id": tx_id,
        "amount":        amount,
        "currency":      currency,
        "customer":      customer_id,
        "invoice_id":    invoice_id,
        "message":       f"Stripe {action} of {currency} {amount:.2f} executed successfully.",
    }
