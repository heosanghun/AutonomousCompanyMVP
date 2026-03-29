"""Webhook alerts for operational incidents (Slack/Discord support)."""

from __future__ import annotations

import json
import os
import urllib.request


def _build_slack_payload(event: str, payload: dict) -> dict:
    """Convert event and payload into a Slack-compatible Block Kit message."""
    color = "#FF0000" if "error" in event.lower() or "fail" in event.lower() or "kill" in event.lower() else "#36A64F"
    
    # Flatten the dict for display
    details = "\n".join(f"*{k}*: {v}" for k, v in payload.items())
    
    return {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 Ops Alert: {event}" if color == "#FF0000" else f"ℹ️ Ops Notice: {event}"
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
            }
        ]
    }


def send_alert(event: str, payload: dict) -> bool:
    """Send alert to webhook if configured; fail silently."""
    url = os.environ.get("OPS_ALERT_WEBHOOK_URL", "").strip()
    if not url:
        return False
        
    # Standardize output for Slack/Discord Webhooks
    if "slack.com" in url or "discord.com/api/webhooks" in url:
        # Discord usually accepts slack compatible payloads if appended with /slack
        # Or we can just send standard JSON. We'll send standard Slack format which Discord accepts via /slack
        body_dict = _build_slack_payload(event, payload)
    else:
        body_dict = {"event": event, "payload": payload}

    body = json.dumps(body_dict, ensure_ascii=True).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=8):
            return True
    except Exception as e:
        print(f"Alert failed to send: {e}")
        return False
