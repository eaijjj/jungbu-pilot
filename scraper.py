import json
import re
import socket
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))

def scrape_all():
    all_data = []
    today_md = datetime.now(KST).strftime("%m-%d")

    # www.ds-pilot.co.kr의 IP를 조회하여 www 없는 도메인 리다이렉트 DNS 오류 방지
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

        # 1. 평택당진도선사회
        try:
            page.goto("http://ptpilot.co.kr", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            rows = page.locator("table tr").all()
            pt_count = 0
            for r in rows:
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if len(cells) >= 10:
                    date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                    time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                    if date_idx != -1 and time_idx != -1 and len(cells) > time_idx + 4:
                        offset = 1 if cells[time_idx + 1] == "" or len(cells[time_idx + 1]) > 3 else 2
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

        # 2. 인천항도선사회
        try:
            page.goto("http://incheonpilot.com", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            rows = page.locator("table tr").all()
            ic_count = 0
            for r in rows:
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if len(cells) >= 6 and cells.isdigit():
                    time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                    if time_idx != -1 and len(cells) > time_idx + 2:
                        vessel = cells[time_idx + 1]
                        route = next((v for v in cells[time_idx+2:time_idx+5] if "-" in v), cells[time_idx + 2])
                        all_data.append({
                            "port": "인천",
                            "vessel": vessel,
                            "callSign": "-",
                            "station": route,
                            "time": f"{today_md} {cells[time_idx]}"
                        })
                        ic_count += 1
            print(f"인천 수집: {ic_count}건")
        except Exception as e:
            print("인천 오류:", e)

        # 3. 대산항도선사회
        try:
            page.goto("http://ds-pilot.co.kr", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            rows = page.locator("table tr").all()
            ds_count = 0
            for r in rows:
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
            print(f"대산 수집: {ds_count}건")
        except Exception as e:
            print("대산 오류:", e)

        browser.close()

    output = {
        "updatedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "schedules": all_data
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_all()
