import os
import json
import urllib.request
from typing import Optional, Dict, Any, List
from pathlib import Path

class AlertManager:
    """
    OpenClaw 스타일의 멀티 채널 게이트웨이.
    Slack, Telegram 등 다양한 채널로 인터랙티브 알림을 전송합니다.
    """
    def __init__(self, slack_webhook: str = None, telegram_token: str = None, telegram_chat_id: str = None):
        self.slack_webhook = slack_webhook or os.getenv("OPS_ALERT_WEBHOOK_URL")
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def send_interactive_alert(self, title: str, message: str, action_id: str, level: str = "info"):
        """Slack Block Kit 또는 Telegram Inline Keyboard를 사용해 인터랙티브 알림을 전송합니다."""
        color = "#81ecff" if level == "info" else "#ff7076"
        results = []
        
        if self.slack_webhook:
            results.append(self._send_slack_block_kit(title, message, action_id, color))
        
        if self.telegram_token and self.telegram_chat_id:
            results.append(self._send_telegram_inline(title, message, action_id))
        
        return any(results) if results else False

    def _send_slack_block_kit(self, title: str, message: str, action_id: str, color: str):
        """Slack 전용 Block Kit 메시지 전송"""
        payload = {
            "attachments": [{
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"🚨 {title}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{message}*"}
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Approve ✅"},
                                "style": "primary",
                                "value": action_id,
                                "action_id": f"approve_{action_id}"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Reject ❌"},
                                "style": "danger",
                                "value": action_id,
                                "action_id": f"reject_{action_id}"
                            }
                        ]
                    }
                ]
            }]
        }
        return self._post_json(self.slack_webhook, payload)

    def _send_telegram_inline(self, title: str, message: str, action_id: str):
        """Telegram 전용 Inline Keyboard 메시지 전송"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": f"🚨 *{title}*\n\n{message}",
            "parse_mode": "Markdown",
            "reply_markup": {
                "inline_keyboard": [[
                    {"text": "Approve ✅", "callback_data": f"approve_{action_id}"},
                    {"text": "Reject ❌", "callback_data": f"reject_{action_id}"}
                ]]
            }
        }
        return self._post_json(url, payload)

    def _post_json(self, url: str, payload: Dict[str, Any]):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as res:
                return res.status == 200
        except Exception as e:
            print(f"Alert failed: {e}")
            return False

# 글로벌 인스턴스 생성
alerts = AlertManager()

def send_alert(message: str, title: str = "System Alert", level: str = "info", approval_id: Optional[str] = None):
    """기존 코드와의 호환성을 위한 래퍼 함수"""
    if approval_id:
        return alerts.send_interactive_alert(title, message, approval_id, level)
    else:
        # 단순 알림 전송 (승인 버튼 없이)
        # Slack/Telegram 단순 메시지 로직 구현 가능
        return alerts.send_interactive_alert(title, message, "notify_only", level)
