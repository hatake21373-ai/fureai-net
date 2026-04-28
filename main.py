from datetime import datetime
from scraper import scrape_slots, filter_available_slots
from notifier import send_line_message, send_email_message  # ←追加

def build_message(slots):
    reservable = [s for s in slots if s["can_reserve"]]
    phone_only = [s for s in slots if not s["can_reserve"]]

    lines = ["【川崎市ふれあいネット 平日夜間 空き通知】", ""]

    lines.append("■ 予約可能な空き")
    if reservable:
        for s in reservable:
            lines.append(f'{s["date"]} {s["facility"]}')
            lines.append(f'  - {s["time_label"]}：{s["status"]}')
    else:
        lines.append("なし")
    lines.append("")

    lines.append("■ 予約不可（電話対応のみ）な空き")
    if phone_only:
        for s in phone_only:
            lines.append(f'{s["date"]} {s["facility"]}')
            lines.append(f'  - {s["time_label"]}：{s["status"]}')
    else:
        lines.append("なし")
    lines.append("")

    return "\n".join(lines)


def main():
    print(f"[START] {datetime.now().isoformat()}")

    results = scrape_slots()
    available = filter_available_slots(results)

    print("総取得件数:", len(results))
    print("空き件数:", len(available))

    if available:
        message = build_message(available)
        print(message)

        # LINE通知
        send_line_message(message)

        # メール通知
        send_email_message(
            subject="【川崎市ふれあいネット】平日夜間 空き通知",
            body=message
        )
    else:
        print("空きはありませんでした。")

    print(f"[END] {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
