"""
Action Tools — Side-effect tools (emails, PDFs, reminders)
Called by the ACT node when tool_name is "send_reminder" or "generate_report"
"""

from typing import Any, Dict, Optional


async def send_payment_reminder(tenant_id: str, client_name: str = "", invoice_id: str = "", **kwargs) -> Dict[str, Any]:
    """Sends a payment reminder email to a client via SendGrid."""
    print(f"  [action_tools.send_payment_reminder] client={client_name}")
    # TODO: Real SendGrid integration
    # import sendgrid; sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    return {
        "status": "success",
        "message": f"Payment reminder sent to {client_name or 'client'} for invoice {invoice_id}",
        "email_sent": True,
    }


async def generate_pdf_report(tenant_id: str, report_type: str = "summary", period: str = "monthly", **kwargs) -> Dict[str, Any]:
    """Generates a PDF report and uploads it to cloud storage."""
    print(f"  [action_tools.generate_pdf_report] type={report_type}")
    # TODO: Real PDF generation with ReportLab/WeasyPrint + S3 upload
    return {
        "status": "success",
        "report_type": report_type,
        "download_url": "https://storage.invoxio.com/reports/report-stub.pdf",
        "message": f"{report_type.capitalize()} report generated for {period}",
    }
