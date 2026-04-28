from playwright.sync_api import sync_playwright
from datetime import date, timedelta
import calendar
import jpholiday
import re

START_URL = "https://www.fureai-net.city.kawasaki.jp/user/view/user/homeIndex.html"


def get_first_day_of_next_month(base_date: date) -> date:
    year = base_date.year
    month = base_date.month

    if month > 12:
        month = 1
        year += 1

    return date(year, month, 1)


def get_end_of_month_three_months_later(base_date: date) -> date:
    year = base_date.year
    month = base_date.month + 3

    while month > 12:
        month -= 12
        year += 1

    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def get_target_dates(base_date: date):
    start_date = get_first_day_of_next_month(base_date)
    end_date = get_end_of_month_three_months_later(base_date)
    dates = []
    current = start_date

    while current <= end_date:
        if current.weekday() < 5 and not jpholiday.is_holiday(current):
            dates.append(current)
        current += timedelta(days=1)

    return dates


def open_search_result(page):
    page.goto(START_URL)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)

    page.locator('a:has(img[alt="目的や人数から"])').click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    print("「目的や人数から」をクリックしました")

    page.get_by_role("checkbox", name="バレーボール", exact=True).check()
    page.wait_for_timeout(1000)
    print("「バレーボール」にチェックしました")

    page.get_by_role("button", name="上記の内容で検索する", exact=True).click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    print("「上記の内容で検索する」をクリックしました")


def read_calendar_year_month(page):
    text = page.inner_text("body")
    m = re.search(r"(\d{4})年(\d{1,2})月", text)
    if not m:
        raise ValueError("カレンダーの年月を取得できませんでした")
    return int(m.group(1)), int(m.group(2))


def move_calendar_to_target_month(page, target_date):
    while True:
        current_year, current_month = read_calendar_year_month(page)
        current_ym = current_year * 100 + current_month
        target_ym = target_date.year * 100 + target_date.month

        if current_ym == target_ym:
            return

        if current_ym < target_ym:
            page.get_by_role("link", name="次月", exact=True).click()
        else:
            page.get_by_role("link", name="前月", exact=True).click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)


def click_day_on_calendar(page, target_date):
    day_str = str(target_date.day)
    links = page.get_by_role("link", name=day_str, exact=True)
    count = links.count()

    if count == 0:
        raise ValueError(f"日付リンク {day_str} が見つかりませんでした")

    for i in range(count):
        link = links.nth(i)
        try:
            if link.is_visible():
                link.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)
                return
        except Exception:
            pass

    raise ValueError(f"日付リンク {day_str} は見つかりましたがクリックできませんでした")


def set_search_date(page, target_date):
    move_calendar_to_target_month(page, target_date)
    click_day_on_calendar(page, target_date)
    print(f"{target_date.isoformat()} をカレンダーで選択しました")


def click_next_5_if_exists(page) -> bool:
    links = page.get_by_role("link", name="次の5件", exact=True)
    count = links.count()

    if count == 0:
        return False

    for i in range(count):
        try:
            link = links.nth(i)
            if link.is_visible():
                link.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(1500)
                print("「次の5件」をクリックしました")
                return True
        except Exception:
            pass

    return False


def collect_current_page_slots(page, target_date):
    results = []

    blocks = page.locator("table.tablebg2")
    block_count = blocks.count()

    for i in range(block_count):
        block = blocks.nth(i)

        if block.locator("span#bnamem").count() == 0 or block.locator("span#inamem").count() == 0:
            continue

        try:
            bname = block.locator("span#bnamem").first.inner_text().strip()
            iname = block.locator("span#inamem").first.inner_text().strip()
            facility_name = f"{bname}／{iname}"
        except Exception:
            continue

        can_reserve = block.locator('input[id="doAddCart"]').count() > 0
        reserve_note = ""
        if not can_reserve and block.locator('div[id="isNotAddCartEnable"]').count() > 0:
            reserve_note = block.locator('div[id="isNotAddCartEnable"]').first.inner_text().strip()

        time_labels = []
        tzones = block.locator("span#tzonename")
        for j in range(tzones.count()):
            label = tzones.nth(j).inner_text().strip()
            if label:
                time_labels.append(label)

        state_icons = block.locator('img[id="emptyStateIcon"]')
        states = []
        for j in range(state_icons.count()):
            alt = state_icons.nth(j).get_attribute("alt") or ""
            states.append(alt.strip())

        slot_count = min(len(time_labels), len(states))
        for j in range(slot_count):
            results.append({
                "date": target_date.isoformat(),
                "facility": facility_name,
                "time_label": time_labels[j],
                "status": states[j],
                "can_reserve": can_reserve,
                "reserve_note": reserve_note,
            })

    print(f"{target_date.isoformat()} の現在ページ分を取得: {len(results)}件")
    return results


def collect_all_slots_for_one_day(page, target_date):
    day_results = []

    while True:
        page_results = collect_current_page_slots(page, target_date)
        day_results.extend(page_results)

        moved = click_next_5_if_exists(page)
        if not moved:
            break

    return day_results


def is_night_slot(time_label: str) -> bool:
    return time_label == "夜間"


def filter_available_slots(slots):
    return [
        s for s in slots
        if s["status"] == "空き" and is_night_slot(s["time_label"])
    ]


def scrape_slots():
    base_date = date.today()
    target_dates = get_target_dates(base_date)

    print("対象日一覧")
    for d in target_dates:
        print(d.isoformat())

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        open_search_result(page)

        for target_date in target_dates:
            print("=" * 50)
            print(f"{target_date} の確認を開始")

            set_search_date(page, target_date)
            day_results = collect_all_slots_for_one_day(page, target_date)
            all_results.extend(day_results)

            print(f"{target_date} の取得件数: {len(day_results)}")

        browser.close()

    return all_results


if __name__ == "__main__":
    results = scrape_slots()
    available = filter_available_slots(results)

    print("総取得件数:", len(results))
    print("空き件数:", len(available))

    for r in available[:20]:
        print(
            f'{r["date"]} | {r["facility"]} | {r["time_label"]} | '
            f'{r["status"]} | 予約可={r["can_reserve"]}'
        )
