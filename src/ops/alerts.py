"""Webhook alerts for operational incidents (Slack/Discord support)."""

from __future__ import annotations

import json
import os
import urllib.request


def _build_slack_payload(event: str, payload: dict, approval_id: str = None) -> dict:
    """Convert event and payload into a Slack-compatible Block Kit message."""
    color = "#FF0000" if "error" in event.lower() or "fail" in event.lower() or "kill" in event.lower() else "#36A64F"
    if approval_id:
        color = "#FFCC00"  # Warning/Action required color
    
    # Flatten the dict for display
    details = "\n".join(f"*{k}*: {v}" for k, v in payload.items())
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 Ops Alert: {event}" if color == "#FF0000" else (f"⚠️ Action Required: {event}" if approval_id else f"ℹ️ Ops Notice: {event}")
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": details or "_No additional details provided._"
            }
        }
    ]

    if approval_id:
        blocks.append({
            "type": "actions",
            "block_id": f"approval_actions_{approval_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Approve"
                    },
                    "style": "primary",
                    "value": f"approve_{approval_id}"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Reject"
                    },
                    "style": "danger",
                    "value": f"reject_{approval_id}"
                }
            ]
        })

    return {
        "attachments": [
            {
                "color": color,
                "blocks": blocks
            }
        ]
    }


def send_alert(event: str, payload: dict, approval_id: str = None) -> bool:
    """Send alert to webhook if configured; fail silently."""
    url = os.environ.get("OPS_ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return False
        
    # Standardize output for Slack/Discord Webhooks
    if "slack.com" in url or "discord.com/api/webhooks" in url:
        # Discord usually accepts slack compatible payloads if appended with /slack
        # Or we can just send standard JSON. We'll send standard Slack format which Discord accepts via /slack
        body_dict = _build_slack_payload(event, payload, approval_id)
    else:
        body_dict = {"event": event, "payload": payload}
        if approval_id:
            body_dict["approval_id"] = approval_id

    body = json.dumps(body_dict, ensure_ascii=True).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=8):
            return True
    except Exception as e:
        print(f"Alert failed to send: {e}")
        return False
