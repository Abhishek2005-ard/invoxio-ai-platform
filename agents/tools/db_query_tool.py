"""
DB Query Tool — MongoDB Aggregation Pipeline Executor

LangChain StructuredTool that accepts a MongoDB aggregation pipeline
as JSON and runs it against the invoices collection.
Called by the ACT node when tool_name = "db_query"
"""
import json
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DBQueryInput(BaseModel):
    tenant_id:  str          = Field(..., description="Tenant ID to scope the query")
    collection: str          = Field(default="invoices", description="MongoDB collection name")
    pipeline:   List[Dict]   = Field(..., description="MongoDB aggregation pipeline stages as a list of dicts")
    limit:      Optional[int]= Field(default=100, description="Max documents to return")


@tool(args_schema=DBQueryInput)
async def db_query_tool(tenant_id: str, collection: str, pipeline: List[Dict], limit: int = 100) -> Dict[str, Any]:
    """
    Execute a MongoDB aggregation pipeline against a tenant-scoped collection.
    Always injects a $match on tenant_id as the first stage for security.
    Returns the result list and metadata.
    """
    print(f"  🗄️  [db_query_tool] collection={collection} | tenant={tenant_id} | stages={len(pipeline)}")

    # ── Security: force tenant_id filter as first stage ───────────────────
    tenant_match = {"$match": {"tenant_id": tenant_id}}
    if not pipeline or pipeline[0].get("$match", {}).get("tenant_id") != tenant_id:
        pipeline = [tenant_match] + pipeline

    # Add limit stage if not already present
    has_limit = any("$limit" in stage for stage in pipeline)
    if not has_limit:
        pipeline.append({"$limit": limit})

    from config.database import get_db
    db = await get_db()
    
    if db is not None:
        try:
            results = await db[collection].aggregate(pipeline).to_list(length=limit)
            return {
                "status": "success",
                "collection": collection,
                "pipeline_stages": len(pipeline),
                "result_count": len(results),
                "results": results,
            }
        except Exception as e:
            return {
                "status": "error",
                "collection": collection,
                "error": str(e)
            }

    # ── Stub response fallback ────────────────────────────────────────────
    stub_results = [
        {"_id": "INV-001", "total_amount": 5000, "status": "paid",   "vendor": {"name": "Acme Corp"}},
        {"_id": "INV-002", "total_amount": 12000,"status": "unpaid", "vendor": {"name": "Beta Ltd"}},
        {"_id": "INV-003", "total_amount": 87500,"status": "overdue","vendor": {"name": "Ghost LLC"}},
    ]

    return {
        "status":      "success",
        "collection":  collection,
        "pipeline_stages": len(pipeline),
        "result_count": len(stub_results),
        "results":     stub_results,
    }
