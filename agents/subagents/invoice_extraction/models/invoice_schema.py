"""
Invoice Data — Pydantic Schema

Defines the exact structured JSON format that Gemini must output.
Used by the validate_output node to confirm the parsed data is complete.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class LineItem(BaseModel):
    """A single line item on an invoice."""
    description: str
    quantity:    Optional[float] = 1.0
    unit_price:  Optional[float] = 0.0
    total:       Optional[float] = 0.0


class VendorInfo(BaseModel):
    """The company that issued the invoice."""
    name:    str
    address: Optional[str] = None
    email:   Optional[str] = None
    phone:   Optional[str] = None
    tax_id:  Optional[str] = None


class ClientInfo(BaseModel):
    """The company being billed."""
    name:    str
    address: Optional[str] = None
    email:   Optional[str] = None


class InvoiceData(BaseModel):
    """
    Fully structured invoice extracted from PDF/image.
    This is the final output of the Invoice Extraction Sub-Agent.
    """
    # Identifiers
    invoice_number:  str
    purchase_order:  Optional[str] = None

    # Parties
    vendor:  VendorInfo
    client:  ClientInfo

    # Dates
    invoice_date:  Optional[str] = None   # ISO format: "2024-03-15"
    due_date:      Optional[str] = None
    payment_terms: Optional[str] = None   # e.g. "Net 30"

    # Line Items
    line_items: List[LineItem] = Field(default_factory=list)

    # Financials
    subtotal:      Optional[float] = 0.0
    tax_rate:      Optional[float] = 0.0  # As percentage, e.g. 18.0 for 18%
    tax_amount:    Optional[float] = 0.0
    discount:      Optional[float] = 0.0
    total_amount:  float
    currency:      str = "USD"

    # Payment
    payment_method:      Optional[str] = None  # "bank_transfer" | "card" | "upi"
    bank_account:        Optional[str] = None
    bank_ifsc:           Optional[str] = None

    # Notes
    notes:     Optional[str] = None
    status:    str = "unpaid"   # "unpaid" | "paid" | "overdue"

    # Extraction Metadata
    ocr_method:        Optional[str] = None
    extraction_confidence: Optional[float] = None
    raw_text_preview:  Optional[str] = None  # First 200 chars of OCR text

    @field_validator("total_amount", mode="before")
    @classmethod
    def parse_total(cls, v):
        """Handles values like '$1,234.56' or '1234.56'."""
        if isinstance(v, str):
            cleaned = v.replace("$", "").replace(",", "").replace("₹", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return v or 0.0
