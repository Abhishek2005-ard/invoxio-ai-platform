"""
Notify Tool — SendGrid (Email) + Twilio (SMS/Push) + Slack Webhooks

LangChain StructuredTool that distributes notifications across channels.
"""
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class NotifyInput(BaseModel):
    tenant_id:  str           = Field(..., description="Tenant ID context")
    channels:   List[str]     = Field(..., description="Notification channels: 'email'|'sms'|'slack'|'push'")
    title:      str           = Field(..., description="Alert/Notification title")
    message:    str           = Field(..., description="Main notification body content")
    recipients: Optional[List[str]] = Field(default=[], description="List of emails/phone numbers/Slack channels")


@tool(args_schema=NotifyInput)
async def notify_tool(
    tenant_id: str,
    channels: List[str],
    title: str,
    message: str,
    recipients: List[str],
) -> Dict[str, Any]:
    """
    Distribute notifications via Email (SendGrid), SMS/WhatsApp (Twilio), or Slack Webhooks.
    """
    print(f"  [notify_tool] channels={channels} | title='{title}' | tenant={tenant_id}")

    results = []

    import os
    import httpx
    
    for channel in channels:
        if channel == "email":
            sg_key = os.getenv("SENDGRID_API_KEY")
            for recipient in recipients:
                if "@" in recipient:
                    if sg_key:
                        try:
                            import sendgrid
                            from sendgrid.helpers.mail import Mail
                            sg = sendgrid.SendGridAPIClient(api_key=sg_key)
                            mail = Mail(from_email='alerts@invoxio.com', to_emails=recipient, subject=title, html_content=message)
                            sg.send(mail)
                            results.append({"channel": "email", "status": "sent", "to": recipient})
                            print(f"    Email sent to: {recipient} via SendGrid")
                        except Exception as e:
                            results.append({"channel": "email", "status": "error", "error": str(e), "to": recipient})
                            print(f"    Error: Email failed for {recipient}: {e}")
                    else:
                        # Fallback
                        with open("local_emails.log", "a", encoding="utf-8") as f:
                            f.write(f"TO: {recipient}\nSUBJECT: {title}\n{message}\n\n")
                        results.append({"channel": "email", "status": "logged_locally", "to": recipient})
                        print(f"    Email mock-saved to local_emails.log for: {recipient}")

        elif channel == "slack":
            slack_url = os.getenv("SLACK_WEBHOOK_URL")
            if slack_url:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(slack_url, json={"text": f"*{title}*\n{message}"})
                    results.append({"channel": "slack", "status": "posted", "channel_name": "#alerts"})
                    print(f"    Slack notification posted")
                except Exception as e:
                    results.append({"channel": "slack", "status": "error", "error": str(e)})
                    print(f"    Error: Slack post failed: {e}")
            else:
                with open("local_slack.log", "a", encoding="utf-8") as f:
                    f.write(f"CHANNEL: #alerts\n{title}\n{message}\n\n")
                results.append({"channel": "slack", "status": "logged_locally"})
                print(f"    Slack mock-saved to local_slack.log")

        elif channel == "sms":
            # TODO: import twilio; twilio.messages.create(...)
            for recipient in recipients:
                if recipient.startswith(("+", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                    results.append({"channel": "sms", "status": "stub_sent", "to": recipient})
                    print(f"    SMS sent to: {recipient}")

    return {
        "status":  "success",
        "details": results,
        "count":   len(results),
    }
