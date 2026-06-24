"""Report Generation Sub-Agent — State"""
from typing import TypedDict, List, Dict, Any, Optional

class ReportGenerationState(TypedDict):
    # Input
    tenant_id:      str
    report_type:    str     # "monthly_summary"|"quarterly_bi"|"overdue_invoices"|"custom"
    period_label:   str     # "March 2024", "Q1 2024"
    date_from:      str
    date_to:        str
    recipients:     List[str]      # email addresses
    channels:       List[str]      # ["email","slack","save"]
    custom_prompt:  Optional[str]  # custom report instructions

    # gather_data node
    bi_data:        Dict[str, Any]  # Revenue, cash flow, top clients, etc.
    anomaly_summary: Dict[str, Any] # Quick anomaly stats

    # generate_content node
    report_sections: List[Dict[str, Any]]  # [{title, content, data}]
    executive_summary: str

    # render_pdf node
    pdf_bytes:      Optional[bytes]
    pdf_filename:   str

    # distribute node
    distribution_results: List[Dict[str, Any]]  # [{channel, status, detail}]

    error:          Optional[str]
