import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate


# =========================
# LINE通知
# =========================
def send_line_message(message: str):
    """
    LINE Notify を使ってメッセージ送信
    必要な環境変数:
      - LINE_NOTIFY_TOKEN
    """
    line_token = os.getenv("LINE_NOTIFY_TOKEN")

    if not line_token:
        print("[WARN] LINE_NOTIFY_TOKEN が未設定のため、LINE通知をスキップします。")
        return

    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {line_token}"
    }
    data = {
        "message": "\n" + message
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=15)
        print(f"[LINE] status={response.status_code}")

        if response.status_code != 200:
            print("[LINE ERROR]", response.text)

    except Exception as e:
        print("[LINE EXCEPTION]", str(e))


# =========================
# メール通知
# =========================
def send_email_message(subject: str, body: str):
    """
    Gmail SMTP を使ってメール送信
    必要な環境変数:
      - SMTP_USER       : 送信元Gmailアドレス
      - SMTP_PASSWORD   : Gmailアプリパスワード
      - MAIL_TO         : 送信先メールアドレス
    任意:
      - SMTP_HOST       : デフォルト smtp.gmail.com
      - SMTP_PORT       : デフォルト 587
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_to = os.getenv("MAIL_TO")

    if not smtp_user or not smtp_password or not mail_to:
        print("[WARN] メール設定不足のため、メール通知をスキップします。")
        print(f"[DEBUG] SMTP_USER={bool(smtp_user)}, SMTP_PASSWORD={bool(smtp_password)}, MAIL_TO={bool(mail_to)}")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = mail_to
    msg["Date"] = formatdate(localtime=True)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [mail_to], msg.as_string())

        print("[MAIL] 送信成功")

    except Exception as e:
        print("[MAIL ERROR]", str(e))
