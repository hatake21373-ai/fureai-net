import os
import requests


def send_line_message(message: str):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN が設定されていません。")

    group_ids_raw = os.getenv("LINE_GROUP_IDS", os.getenv("LINE_GROUP_ID", "")).strip()
    group_ids = [gid.strip() for gid in group_ids_raw.split(",") if gid.strip()]

    if not group_ids:
        raise RuntimeError("LINE_GROUP_IDS または LINE_GROUP_ID が設定されていません。")

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    errors = []
    success_count = 0

    for group_id in group_ids:
        payload = {
            "to": group_id,
            "messages": [
                {
                    "type": "text",
                    "text": message[:5000],
                }
            ],
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"LINE status ({group_id}):", res.status_code)
            print(f"LINE response ({group_id}):", res.text)

            if res.ok:
                success_count += 1
            else:
                errors.append(f"{group_id}: {res.status_code} {res.text}")

        except requests.RequestException as e:
            errors.append(f"{group_id}: request error {e}")

    print(f"LINE通知成功件数: {success_count}/{len(group_ids)}")

    if errors:
        raise RuntimeError("LINE通知に失敗したグループがあります:\n" + "\n".join(errors))
