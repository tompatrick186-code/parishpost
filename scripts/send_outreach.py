"""
Parish Post — Cold email outreach to parish council clerks
Reads parishes.csv, sends emails via Resend, marks as emailed
"""

import csv
import resend
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

RESEND_API_KEY = "re_b3mS6XEa_6brYrjCk8XJ4A1FUJkK4Moap"
FROM_EMAIL     = "hello@theparishpost.co.uk"
FROM_NAME      = "Tom at Parish Post"

resend.api_key = RESEND_API_KEY

SUBJECT = "Free newsletter for {parish} — no work required"

BODY_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:Georgia,serif;background:#FAF7F2;margin:0;padding:0}}
.wrap{{max-width:580px;margin:40px auto;background:#fff;border:1px solid #e8e0d0}}
.header{{background:#8B1A1A;padding:24px 32px}}
.logo{{font-size:20px;color:#fff;font-family:Georgia,serif}}
.logo span{{color:#C4B99A;font-style:italic}}
.body{{padding:32px;color:#1A1A14;font-size:15px;line-height:1.8}}
.body p{{margin:0 0 16px}}
.footer{{padding:16px 32px;border-top:1px solid #e8e0d0;font-family:sans-serif;font-size:11px;color:#9e9e8e}}
</style></head><body>
<div class="wrap">
<div class="header"><div class="logo">Parish<span>Post</span></div></div>
<div class="body">
<p>Dear {parish} Clerk,</p>
<p>I'm Tom from Parish Post. We write monthly newsletters for parish councils across England — you tell us the news and events, we turn it into a polished, ready-to-send newsletter within the hour.</p>
<p>No writing. No design. No software. Just fill in a short form each month.</p>
<p><strong>I'd like to write your first newsletter completely free</strong> — no commitment, no card required — so you can see exactly what you get before deciding anything.</p>
<p>If you'd like to give it a try, just reply to this email or visit:<br>
<a href="https://theparishpost.co.uk/order.html" style="color:#8B1A1A">theparishpost.co.uk/order.html</a></p>
<p>Happy to answer any questions.</p>
<p>Best wishes,<br>Tom<br>Parish Post<br>hello@theparishpost.co.uk</p>
</div>
<div class="footer">Parish Post &middot; <a href="mailto:hello@theparishpost.co.uk" style="color:#8B1A1A">hello@theparishpost.co.uk</a></div>
</div></body></html>"""


def send_outreach(csv_file="parishes.csv", batch_size=50):
    rows = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    sent = 0
    for i, row in enumerate(rows):
        if row.get("emailed") == "yes":
            continue
        if sent >= batch_size:
            print(f"\nBatch limit reached — {sent} emails sent today.")
            break

        email = row["email"].strip()
        parish = row["name"].strip()

        try:
            resend.Emails.send({
                "from":    f"{FROM_NAME} <{FROM_EMAIL}>",
                "to":      [email],
                "subject": SUBJECT.format(parish=parish),
                "html":    BODY_HTML.format(parish=parish),
            })
            rows[i]["emailed"] = "yes"
            sent += 1
            print(f"  Sent to {parish} <{email}>")
        except Exception as e:
            print(f"  Error sending to {email}: {e}")

    if rows:
        fieldnames = list(rows[0].keys())
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"\nDone — {sent} emails sent.")


if __name__ == "__main__":
    send_outreach()
