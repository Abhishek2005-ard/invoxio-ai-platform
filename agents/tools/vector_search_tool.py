"""
Vector Search Tool — Semantic RAG

LangChain StructuredTool that performs semantic search against the
knowledge base (e.g. invoice PDFs, vendor payment terms, policy docs).
Uses Pinecone for vector indexing and Gemini for embeddings.
"""
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class VectorSearchInput(BaseModel):
    tenant_id:  str           = Field(..., description="Tenant ID to scope the vector search")
    query:      str           = Field(..., description="Semantic search query")
    namespace:  str           = Field(default="invoices", description="Vector index namespace: 'invoices'|'policies'|'vendors'")
    top_k:      Optional[int] = Field(default=5, description="Number of matches to return")


@tool(args_schema=VectorSearchInput)
async def vector_search_tool(
    tenant_id: str,
    query: str,
    namespace: str,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Search vector database (Pinecone) using Gemini embeddings.
    Always scopes results by tenant_id using Pinecone metadata filters.
    """
    print(f"  🔍 [vector_search_tool] namespace={namespace} | query='{query[:50]}' | tenant={tenant_id}")

    # TODO: Replace with Pinecone client + Gemini embeddings:
    # from langchain_google_genai import GoogleGenerativeAIEmbeddings
    # from pinecone import Pinecone
    # pc = Pinecone(api_key=settings.pinecone_api_key)
    # index = pc.Index(settings.pinecone_index)
    # embed = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    # vec = await embed.aembed_query(query)
    # results = index.query(vector=vec, filter={"tenant_id": tenant_id}, namespace=namespace, top_k=top_k)

    # ── Stub response ─────────────────────────────────────────────────────
    stub_matches = [
        {
            "id": "doc-103",
            "score": 0.895,
            "metadata": {"tenant_id": tenant_id, "file_name": "acme_terms.pdf", "page": 2},
            "text": "Acme Corp payment terms are Net 30. Payments must be processed through Chase Bank bank transfer.",
        },
        {
            "id": "doc-207",
            "score": 0.812,
            "metadata": {"tenant_id": tenant_id, "file_name": "company_travel_policy.pdf", "page": 4},
            "text": "Meals during domestic business travel are capped at $75 per day. Receipt must be attached to the invoice.",
        },
    ]

    return {
        "status":     "success",
        "query":      query,
        "namespace":  namespace,
        "matches":    stub_matches,
    }
