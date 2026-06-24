"""
Invoice Tools — LangChain-compatible async functions
Called by the ACT node when tool_name is "invoice_query" or "get_invoice_detail"

These are STUB implementations — replace MongoDB queries here
when the backend database is connected.
"""

from typing import Any, Dict, Optional


async def query_invoices(
    tenant_id: str,
    query: str = "",
    status: Optional[str] = None,
    client_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    filters: Optional[Dict] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Search invoices in MongoDB for a specific tenant.

    Args:
        tenant_id:   Scopes the query to one tenant only
        query:       Natural language query (used for context)
        status:      Filter by: "paid" | "unpaid" | "overdue" | "draft"
        client_name: Filter by client name (partial match)
        date_from:   ISO date string (e.g. "2024-01-01")
        date_to:     ISO date string (e.g. "2024-03-31")

    Returns:
        Dict with invoices list and summary stats
    """
    print(f"  🔍 [invoice_tools.query_invoices] tenant={tenant_id}, status={status}, client={client_name}")

    from config.database import get_db
    db = await get_db()
    
    if db is not None:
        try:
            # Build query filter
            db_filter = {"tenant_id": tenant_id}
            if status:
                db_filter["status"] = status
            if client_name:
                # Basic regex search
                db_filter["client_name"] = {"$regex": client_name, "$options": "i"}
            if date_from or date_to:
                db_filter["invoice_date"] = {}
                if date_from:
                    db_filter["invoice_date"]["$gte"] = date_from
                if date_to:
                    db_filter["invoice_date"]["$lte"] = date_to
                if not db_filter["invoice_date"]:
                    del db_filter["invoice_date"]

            invoices_cursor = db.invoices.find(db_filter).limit(50)
            invoices = await invoices_cursor.to_list(length=50)

            # Compute summary
            total_amount = sum(inv.get("amount", 0) for inv in invoices)
            overdue_count = sum(1 for inv in invoices if inv.get("status") == "overdue")
            paid_count = sum(1 for inv in invoices if inv.get("status") == "paid")

            return {
                "status": "success",
                "total": len(invoices),
                "invoices": invoices,
                "summary": {
                    "total_amount": total_amount,
                    "overdue_count": overdue_count,
                    "paid_count": paid_count
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # STUB: returns sample data for development
    return {
        "status": "success",
        "total": 3,
        "invoices": [
            {"id": "INV-001", "client": "Acme Corp", "amount": 5000, "status": "overdue", "due_date": "2024-03-01"},
            {"id": "INV-002", "client": "Beta Ltd",  "amount": 12000, "status": "paid",    "paid_date": "2024-03-15"},
            {"id": "INV-003", "client": "Acme Corp", "amount": 3200, "status": "unpaid",  "due_date": "2024-04-01"},
        ],
        "summary": {"total_amount": 20200, "overdue_count": 1, "paid_count": 1},
    }


async def get_invoice_detail(
    tenant_id: str,
    invoice_id: str,
    **kwargs,
) -> Dict[str, Any]:
    """
    Retrieve a single invoice with full line-item details.

    Args:
        tenant_id:  Scopes to tenant
        invoice_id: The invoice ID to retrieve
    """
    print(f"  📄 [invoice_tools.get_invoice_detail] id={invoice_id}")

    from config.database import get_db
    db = await get_db()

    if db is not None:
        try:
            invoice = await db.invoices.find_one({"id": invoice_id, "tenant_id": tenant_id})
            if not invoice:
                # Also try matching '_id' if 'id' wasn't found
                invoice = await db.invoices.find_one({"_id": invoice_id, "tenant_id": tenant_id})
            
            if not invoice:
                return {"error": "Not found"}

            return {
                "status": "success",
                "invoice": invoice
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    return {
        "status": "success",
        "invoice": {
            "id": invoice_id,
            "client": "Acme Corp",
            "vendor": "Invoxio Inc",
            "amount": 5000,
            "tax": 900,
            "total": 5900,
            "status": "overdue",
            "due_date": "2024-03-01",
            "line_items": [
                {"description": "Consulting Services", "qty": 10, "rate": 500},
            ],
        },
    }
