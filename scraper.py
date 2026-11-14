import json
import re
import time
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_pyeongtaek():
    results = []
    today_ymd = datetime.now(KST).strftime("%Y%m%d")
    try:
        # 평택: 기본 GET 및 날짜 파라미터 조회 병행
        url = f"http://ptpilot.co.kr{today_ymd}"
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        
        for tr in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 10:
                date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if date_idx != -1 and time_idx != -1 and len(cells) > time_idx + 4:
                    vessel = cells[time_idx + 2]
                    from_pt = cells[time_idx + 3]
                    to_pt = cells[time_idx + 4]
                    call_sign = cells[-1] if re.match(r"^[A-Z0-9]{4,8}$", cells[-1]) else "-"
                    results.append({
                        "port": "평택",
                        "vessel": vessel,
                        "callSign": call_sign,
                        "station": f"{from_pt} → {to_pt}",
                        "time": f"{cells[date_idx]} {cells[time_idx]}"
                    })
        if not results:
            print("평택 HTML 일부:", soup.get_text(" ", strip=True)[:300])
    except Exception as e:
        print("평택 수집 오류:", e)
    return results

def fetch_incheon():
    results = []
    today_ymd = datetime.now(KST).strftime("%Y-%m-%d")
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        url = "http://incheonpilot.com"
        res = requests.post(url, data={"sdate": today_ymd}, headers=HEADERS, timeout=15)
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "html.parser")
        
        for tr in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 6 and cells.isdigit():
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if time_idx != -1 and len(cells) > time_idx + 2:
                    vessel = cells[time_idx + 1]
                    route = next((v for v in cells[time_idx+2:time_idx+5] if "-" in v), cells[time_idx + 2])
                    results.append({
                        "port": "인천",
                        "vessel": vessel,
                        "callSign": "-",
                        "station": route,
                        "time": f"{today_md} {cells[time_idx]}"
                    })
        if not results:
            print("인천 HTML 일부:", soup.get_text(" ", strip=True)[:300])
    except Exception as e:
        print("인천 수집 오류:", e)
    return results

def fetch_daesan():
    results = []
    today_str = datetime.now(KST).strftime("%Y/%m/%d")
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        # 반드시 www.ds-pilot.co.kr 사용 (리다이렉트 방지를 위해 allow_redirects=False 후 처리)
        url = "http://ds-pilot.co.kr"
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        
        for tr in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 5:
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if time_idx != -1 and len(cells) > time_idx + 2:
                    if not cells[time_idx + 1].isdigit():
                        results.append({
                            "port": "대산",
                            "vessel": cells[time_idx + 1],
                            "callSign": "-",
                            "station": cells[time_idx + 2],
                            "time": f"{today_md} {cells[time_idx]}"
                        })
        if not results:
            print("대산 HTML 일부:", soup.get_text(" ", strip=True)[:300])
    except Exception as e:
        print("대산 수집 오류:", e)
    return results

def main():
    all_data = []
    pt = fetch_pyeongtaek()
    print(f"평택 수집: {len(pt)}건")
    all_data.extend(pt)
    time.sleep(2)

    ic = fetch_incheon()
    print(f"인천 수집: {len(ic)}건")
    all_data.extend(ic)
    time.sleep(2)

    ds = fetch_daesan()
    print(f"대산 수집: {len(ds)}건")
    all_data.extend(ds)

    output = {
        "updatedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "schedules": all_data
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
