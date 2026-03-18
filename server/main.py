"""
Parish Post — Newsletter Generation Server
Receives order form submissions, generates newsletters with Claude AI, emails results.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import resend
import anthropic
import os
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
RESEND_API_KEY    = os.environ["RESEND_API_KEY"].strip()
FROM_EMAIL        = "hello@theparishpost.co.uk"
FROM_NAME         = "Tom at Parish Post"
NOTIFY_EMAIL      = "tompatrick186@gmail.com"

resend.api_key = RESEND_API_KEY
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class OrderRequest(BaseModel):
    parish: str
    name: str
    email: str
    residents_email: Optional[str] = ""
    council_news: str
    events: Optional[str] = ""
    community: Optional[str] = ""
    tone: Optional[str] = ""


def generate_newsletter(parish: str, council_news: str, events: str,
                         community: str, tone: str) -> str:
    tone_hint = f"Tone: {tone}. " if tone else "Tone: friendly and warm, but professional. "
    prompt = f"""You are writing a monthly community newsletter for {parish}.

{tone_hint}Write it as a real newsletter editor would — clear, engaging, well-structured.
Do NOT mention AI. Write as if a human editor wrote this.

Content provided by the parish clerk:

COUNCIL NEWS:
{council_news}

UPCOMING EVENTS:
{events if events else "None provided"}

COMMUNITY NOTICES:
{community if community else "None provided"}

Write the full newsletter as HTML. Structure:
- Warm opening paragraph welcoming readers
- Parish Council News section
- Upcoming Events section (if events provided)
- Community Notices section (if notices provided)
- Short friendly sign-off

Use clean HTML with inline styles. Traditional serif feel. Readable in 3 minutes.
Use <h3> for section headings, <p> for paragraphs."""

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def wrap_newsletter_email(parish: str, newsletter_html: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:Georgia,serif;background:#FAF7F2;margin:0;padding:0}}
.wrap{{max-width:620px;margin:40px auto;background:#fff;border:1px solid #e8e0d0}}
.header{{background:#8B1A1A;padding:24px 32px;display:flex;justify-content:space-between;align-items:center}}
.logo{{font-size:20px;color:#fff;font-family:Georgia,serif}}.logo span{{color:#C4B99A;font-style:italic}}
.header-parish{{font-family:sans-serif;font-size:11px;color:rgba(255,255,255,0.7);letter-spacing:0.1em;text-transform:uppercase}}
.body{{padding:32px;color:#1A1A14;font-size:15px;line-height:1.8}}
.body h3{{font-size:0.9rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;border-bottom:1px solid #e8e0d0;padding-bottom:6px;margin:24px 0 12px;font-family:sans-serif}}
.body p{{margin:0 0 14px}}
.footer{{padding:16px 32px;border-top:1px solid #e8e0d0;font-family:sans-serif;font-size:11px;color:#9e9e8e}}
</style></head><body>
<div class="wrap">
<div class="header">
  <div class="logo">Parish<span>Post</span></div>
  <div class="header-parish">{parish}</div>
</div>
<div class="body">
{newsletter_html}
</div>
<div class="footer">Parish Post &middot; <a href="mailto:hello@theparishpost.co.uk" style="color:#8B1A1A">hello@theparishpost.co.uk</a> &middot; <a href="https://theparishpost.co.uk" style="color:#8B1A1A">theparishpost.co.uk</a></div>
</div></body></html>"""


@app.post("/order")
async def receive_order(order: OrderRequest):
    try:
        print(f"Generating newsletter for {order.parish}")
        newsletter_html = generate_newsletter(
            order.parish, order.council_news, order.events,
            order.community, order.tone
        )
        full_email_html = wrap_newsletter_email(order.parish, newsletter_html)

        resend.Emails.send({
            "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
            "to":      [order.email],
            "subject": f"Your {order.parish} newsletter — Parish Post",
            "html":    full_email_html,
        })

        if order.residents_email:
            resend.Emails.send({
                "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
                "to":      [order.residents_email],
                "subject": f"The {order.parish} Newsletter",
                "html":    full_email_html,
            })

        resend.Emails.send({
            "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
            "to":      [NOTIFY_EMAIL],
            "subject": f"Newsletter generated — {order.parish}",
            "html":    f"<p><b>Parish:</b> {order.parish}<br><b>Clerk:</b> {order.name}<br><b>Email:</b> {order.email}</p><p>Newsletter generated and sent.</p>",
        })

        print(f"Done — newsletter sent to {order.email}")
        return {"status": "sent"}

    except Exception as e:
        print(f"Error: {e}")
        resend.Emails.send({
            "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
            "to":      [NOTIFY_EMAIL],
            "subject": f"Newsletter failed — {order.parish}",
            "html":    f"<p>Failed for {order.parish} ({order.email})</p><p>Error: {e}</p>",
        })
        return {"status": "error"}


@app.get("/health")
def health():
    return {"status": "ok"}
