import json
import re
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))

def scrape_all():
    all_data = []
    today_md = datetime.now(KST).strftime("%m-%d")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()

        # 1. 평택당진도선사회
        try:
            page.goto("http://ptpilot.co.kr", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.evaluate("location.href = '/forecast/1'")
            page.wait_for_timeout(3000)

            pt_count = 0
            for frame in page.frames:
                for r in frame.locator("tr").all():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) >= 10:
                        date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                        time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                        if date_idx != -1 and time_idx != -1 and len(cells) > time_idx + 3:
                            next_val = cells[time_idx + 1]
                            is_remark = (next_val == "") or (len(next_val) <= 3 and not re.match(r"^[A-Z]{2,3}$", next_val))
                            offset = 2 if is_remark else 1

                            if len(cells) > time_idx + offset + 2:
                                vessel = cells[time_idx + offset]
                                from_pt = cells[time_idx + offset + 1]
                                to_pt = cells[time_idx + offset + 2]
                                call_sign = cells[-1] if re.match(r"^[A-Z0-9]{4,8}$", cells[-1]) else "-"
                                all_data.append({
                                    "port": "평택",
                                    "vessel": vessel,
                                    "callSign": call_sign,
                                    "station": f"{from_pt} → {to_pt}",
                                    "time": f"{cells[date_idx]} {cells[time_idx]}"
                                })
                                pt_count += 1
            print(f"평택 수집: {pt_count}건")
        except Exception as e:
            print("평택 오류:", e)

        # 2. 인천항도선사회 (인덱스 오타 완전 제거)
        try:
            page.goto("http://incheonpilot.com", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.evaluate("location.href = '/pilot/pilot04_01.asp'")
            page.wait_for_timeout(3000)

            ic_count = 0
            for frame in page.frames:
                for r in frame.locator("tr").all():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) >= 6 and re.match(r"^\d+$", cells):
                        time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                        if time_idx != -1 and len(cells) > time_idx + 2:
                            route = next((v for v in cells[time_idx+2:time_idx+5] if "-" in v), cells[time_idx + 2])
                            all_data.append({
                                "port": "인천",
                                "vessel": cells[time_idx + 1],
                                "callSign": "-",
                                "station": route,
                                "time": f"{today_md} {cells[time_idx]}"
                            })
                            ic_count += 1
            print(f"인천 수집: {ic_count}건")
        except Exception as e:
            print("인천 오류:", e)

        browser.close()

    print(f"총 수집 건수: {len(all_data)}건")
    output = {
        "updatedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "schedules": all_data
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_all()
