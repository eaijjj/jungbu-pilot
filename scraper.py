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
    try:
        # 평택은 기본 GET 요청으로 오늘/내일 스케줄이 모두 조회됨
        url = "http://ptpilot.co.kr"
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        
        for tr in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 10:
                date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if date_idx != -1 and time_idx != -1 and len(cells) > time_idx + 4:
                    # 긴특 칸 유무에 따라 선박명 위치 판별 (긴특 칸이 비어있으면 바로 다음 칸이 선명)
                    offset = 1 if cells[time_idx + 1] == "" or len(cells[time_idx + 1]) > 3 else 2
                    vessel = cells[time_idx + offset]
                    from_pt = cells[time_idx + offset + 1]
                    to_pt = cells[time_idx + offset + 2]
                    call_sign = cells[-1] if re.match(r"^[A-Z0-9]{4,8}$", cells[-1]) else "-"
                    results.append({
                        "port": "평택",
                        "vessel": vessel,
                        "callSign": call_sign,
                        "station": f"{from_pt} → {to_pt}",
                        "time": f"{cells[date_idx]} {cells[time_idx]}"
                    })
    except Exception as e:
        print("평택 수집 오류:", e)
    return results

def fetch_incheon():
    results = []
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        # 인천은 기본 GET 요청으로 오늘 스케줄 조회
        url = "http://incheonpilot.com"
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding
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
    except Exception as e:
        print("인천 수집 오류:", e)
    return results

def fetch_daesan():
    results = []
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        # www. 없는 도메인으로 리다이렉트되는 것을 차단하고 www.ds-pilot.co.kr 직접 호출
        url = "http://ds-pilot.co.kr"
        res = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=False)
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
            print("대산 상태코드:", res.status_code, "응답 일부:", soup.get_text(" ", strip=True)[:200])
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
