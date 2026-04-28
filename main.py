from datetime import datetime
from scraper import scrape_slots, filter_available_slots
from notifier import send_line_message, send_email_message

# =========================
# 設定
# =========================
TARGET_FACILITIES = [
    "高津スポーツセンター",
    "川崎市民プラザ",
]


# =========================
# 通知文作成（空きあり）
# =========================
def build_message(slots):
    reservable = [s for s in slots if s["can_reserve"]]
    phone_only = [s for s in slots if not s["can_reserve"]]

    lines = ["【川崎市ふれあいネット 平日夜間 空き通知】", ""]
    lines.append(f"対象施設: {', '.join(TARGET_FACILITIES)}")
    lines.append("条件: 平日 + 夜間")
    lines.append("")

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


# =========================
# 通知文作成（空きなし）
# =========================
def build_no_slots_message():
    lines = ["【川崎市ふれあいネット 平日夜間 空き通知】", ""]
    lines.append(f"対象施設: {', '.join(TARGET_FACILITIES)}")
    lines.append("条件: 平日 + 夜間")
    lines.append("")
    lines.append("■ 結果")
    lines.append("対象施設の平日夜間に空きはありませんでした。")
    lines.append("")
    return "\n".join(lines)


# =========================
# 判定ロジック
# =========================
def is_target_facility(facility_name: str) -> bool:
    """
    施設名は「高津スポーツセンター／大体育室」などの可能性があるので部分一致
    """
    return any(target in facility_name for target in TARGET_FACILITIES)


def is_weekday(date_str: str) -> bool:
    """
    date_str: '2026-05-01' 形式想定
    月=0, 火=1, 水=2, 木=3, 金=4, 土=5, 日=6
    平日 = 0〜4
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.weekday() < 5
    except Exception as e:
        print(f"[DATE PARSE ERROR] {date_str} -> {e}")
        return False


def is_night_time(time_label: str) -> bool:
    """
    time_label に「夜間」が含まれるものを対象
    例:
      - 夜間
      - 夜間A
      - 夜間（18:00〜21:00）
    """
    return "夜間" in time_label


# =========================
# メイン処理
# =========================
def main():
    print(f"[START] {datetime.now().isoformat()}")

    # 全件取得
    results = scrape_slots()

    # 空きのみ抽出
    available = filter_available_slots(results)

    # 対象施設 + 平日 + 夜間 に絞る
    filtered_available = [
        s for s in available
        if is_target_facility(s["facility"])
        and is_weekday(s["date"])
        and is_night_time(s["time_label"])
    ]

    print("総取得件数:", len(results))
    print("空き件数（全体）:", len(available))
    print("空き件数（対象施設・平日夜間）:", len(filtered_available))

    if filtered_available:
        # 空きあり
        message = build_message(filtered_available)
        print(message)

        # LINE通知（空きありの時だけ）
        try:
            send_line_message(message)
        except Exception as e:
            print("[LINE ERROR]", str(e))

        # メール通知
        try:
            send_email_message(
                subject="【川崎市ふれあいネット】平日夜間 空き通知",
                body=message
            )
        except Exception as e:
            print("[MAIL ERROR]", str(e))
    else:
        # 空きなし
        no_slots_message = build_no_slots_message()
        print(no_slots_message)

        # メールだけ送る（LINEは送らない）
        try:
            send_email_message(
                subject="【川崎市ふれあいネット】平日夜間 空き通知",
                body=no_slots_message
            )
        except Exception as e:
            print("[MAIL ERROR]", str(e))

    print(f"[END] {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
