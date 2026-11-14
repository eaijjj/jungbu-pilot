import json
import re
import socket
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))

def scrape_all():
    all_data = []
    today_md = datetime.now(KST).strftime("%m-%d")

    try:
        ds_ip = socket.gethostbyname("www.ds-pilot.co.kr")
    except Exception:
        ds_ip = "127.0.0.1"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[f"--host-resolver-rules=MAP ds-pilot.co.kr {ds_ip}"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()

        # 1. 평택당진도선사회 (메인 접속 후 '도선예보' 클릭)
        try:
            page.goto("http://www.ptpilot.co.kr/", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            page.locator("a:has-text('도선예보'), a:has-text('예보현황조회')").first.click()
            page.wait_for_timeout(2500)

            pt_count = 0
            for frame in page.frames:
                for r in frame.locator("tr").all():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) >= 10:
                        date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                        time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                        if date_idx != -1 and time_idx != -1 and len(cells) > time_idx + 4:
                            offset = 1 if cells[time_idx + 1] == "" or len(cells[time_idx + 1]) > 3 else 2
                            all_data.append({
                                "port": "평택",
                                "vessel": cells[time_idx + offset],
                                "callSign": cells[-1] if re.match(r"^[A-Z0-9]{4,8}$", cells[-1]) else "-",
                                "station": f"{cells[time_idx + offset + 1]} → {cells[time_idx + offset + 2]}",
                                "time": f"{cells[date_idx]} {cells[time_idx]}"
                            })
                            pt_count += 1
            print(f"평택 수집: {pt_count}건 (이동 URL: {page.url})")
        except Exception as e:
            print("평택 오류:", e)

        # 2. 인천항도선사회 (메인 접속 후 '도선예보현황' 클릭)
        try:
            page.goto("http://www.incheonpilot.com/", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            page.locator("a:has-text('도선예보현황'), a:has-text('예보현황조회')").first.click()
            page.wait_for_timeout(2500)

            ic_count = 0
            for frame in page.frames:
                for r in frame.locator("tr").all():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) >= 6 and cells[0].isdigit():
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
            print(f"인천 수집: {ic_count}건 (이동 URL: {page.url})")
        except Exception as e:
            print("인천 오류:", e)

        # 3. 대산항도선사회 (메인 접속 후 '도선예보현황' 클릭)
        try:
            page.goto("http://www.ds-pilot.co.kr/", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            page.locator("a:has-text('도선예보현황'), a:has-text('도선예보')").first.click()
            page.wait_for_timeout(2500)

            ds_count = 0
            for frame in page.frames:
                for r in frame.locator("tr").all():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) >= 5:
                        time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                        if time_idx != -1 and len(cells) > time_idx + 2 and not cells[time_idx + 1].isdigit():
                            all_data.append({
                                "port": "대산",
                                "vessel": cells[time_idx + 1],
                                "callSign": "-",
                                "station": cells[time_idx + 2],
                                "time": f"{today_md} {cells[time_idx]}"
                            })
                            ds_count += 1
            print(f"대산 수집: {ds_count}건 (이동 URL: {page.url})")
        except Exception as e:
            print("대산 오류:", e)

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
