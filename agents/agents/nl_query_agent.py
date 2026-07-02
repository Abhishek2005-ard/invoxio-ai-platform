"""
NL Query / Analytics Agent  (Natural Language → SQL → Answer)
Translates plain-English financial questions into SQL queries,
executes them against the invoice database context, and returns
a human-readable answer with supporting data.
"""

from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END

# Simulated schema context — replace with real DB introspection
DB_SCHEMA = """
Tables:
  invoices(id, vendor, amount, tax, date, due_date, status, po_number, category)
  vendors(id, name, category, country, contact_email)
  payments(id, invoice_id, paid_at, method, amount_paid)

Sample values:
  status: 'Paid' | 'Pending' | 'Overdue'
  category: 'Marketing' | 'SaaS' | 'Payroll' | 'Legal' | 'Office' | 'Travel'
"""


class NLQueryState(TypedDict):
    question: str
    sql_query: str
    answer: str


async def generate_sql(state: NLQueryState, llm) -> dict:
    """Translate the natural-language question into a SQL query."""
    print("[NL Query Agent] generate_sql")
    prompt = (
        "You are a financial SQL expert. Given the database schema and user question below, "
        "write a single clean SQL SELECT query that answers the question.\n"
        "Return ONLY the SQL query, no explanation.\n\n"
        f"Schema:\n{DB_SCHEMA}\n\n"
        f"Question: {state['question']}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"sql_query": response.content.strip()}


async def answer_from_sql(state: NLQueryState, llm) -> dict:
    """
    Simulate query execution and produce a human-readable answer.
    In production: execute state['sql_query'] against your real DB here.
    """
    print("[NL Query Agent] answer_from_sql")

    # Simulated result data
    simulated_result = (
        "Simulated DB result for: " + state["sql_query"][:80] + "...\n"
        "[Row 1] Globex Corp | Marketing | $12,400\n"
        "[Row 2] ACME Supplies | Marketing | $3,250\n"
        "Total: $15,650"
    )

    prompt = (
        "You are a financial analyst. Given the SQL query and its result below, "
        "write a concise, clear natural-language answer for the user.\n\n"
        f"SQL Query:\n{state['sql_query']}\n\n"
        f"Query Result:\n{simulated_result}\n\n"
        f"Original Question: {state['question']}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"answer": response.content}


def build_nl_query_graph(llm):
    async def _sql(state): return await generate_sql(state, llm)
    async def _answer(state): return await answer_from_sql(state, llm)

    g = StateGraph(NLQueryState)
    g.add_node("generate_sql", _sql)
    g.add_node("answer", _answer)
    g.add_edge(START, "generate_sql")
    g.add_edge("generate_sql", "answer")
    g.add_edge("answer", END)
    return g.compile()


def make_nl_query_tool(llm, dummy: bool = False):
    graph = build_nl_query_graph(llm)

    @tool
    async def nl_query_agent(question: str) -> str:
        """
        Answer natural-language financial questions by generating SQL and returning results.
        Use this for questions like: 'What did we spend on marketing last quarter?',
        'Who are our top 5 vendors by spend?', 'Show all overdue invoices over $5000'.
        """
        print("\n--- [NL Query Agent triggered] ---")
        if dummy:
            return f"[Mock] Answer for: '{question}'\nTop marketing vendors: Globex Corp ($12,400), ACME Supplies ($3,250). Total: $15,650."
        result = await graph.ainvoke({"question": question, "sql_query": "", "answer": ""})
        return result["answer"]

    return nl_query_agent
