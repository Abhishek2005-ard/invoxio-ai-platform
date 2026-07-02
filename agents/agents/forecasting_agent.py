"""
Forecasting Agent
Responsible for: projecting future revenue / cash flow given
an initial amount, a monthly growth rate, and a time horizon.
"""

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool


def make_forecasting_tool(llm, dummy: bool = False):
    """Return a @tool-decorated function for revenue forecasting."""

    @tool
    async def forecasting_subagent(
        current_revenue: float,
        growth_rate: float,
        months: int
    ) -> str:
        """
        Predict future revenue or cash flow.

        Args:
            current_revenue: Starting revenue figure (e.g. 100000.0).
            growth_rate: Monthly growth rate as a percentage (e.g. 5.0 for 5 %).
            months: Number of months to forecast (e.g. 12).
        """
        print("\n--- [Forecasting Agent triggered] ---")
        if dummy:
            return f"[Mock] Forecast for {months} months at {growth_rate}% growth."

        prompt = (
            f"Project monthly revenue for {months} months "
            f"starting from ${current_revenue:,.2f} "
            f"with a compound monthly growth rate of {growth_rate}%.\n"
            "Show a month-by-month table and a final projected total. Keep it concise."
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    return forecasting_subagent
