import json
import time
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_pyeongtaek():
    results = []
    try:
        res = requests.get("http://ptpilot.co.kr", headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        for tr in soup.select("table tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            # 평택 표 구조: [0]번호 [1]상태 [2]도선사 [3]일자 [4]시간 [5]긴특 [6]선명 [7]출발 [8]도착 ... [14]호출부호
            if len(tds) >= 15 and "-" in tds[3] and ":" in tds[4]:
                date_str = tds[3]
                time_str = tds[4]
                vessel = tds[6]
                from_pt = tds[7]
                to_pt = tds[8]
                call_sign = tds[14] if tds[14] else "-"
                results.append({
                    "port": "평택",
                    "vessel": vessel,
                    "callSign": call_sign,
                    "station": f"{from_pt} → {to_pt}",
                    "time": f"{date_str} {time_str}"
                })
    except Exception as e:
        print("평택 수집 오류:", e)
    return results

def fetch_incheon():
    results = []
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        res = requests.get("http://incheonpilot.com", headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")
        for tr in soup.select("table tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            # 인천 표 구조: [0]No [1]도선사 [2]시간 [3]선명 [4]갑문 [5]도선구간 ...
            if len(tds) >= 6 and tds[0].isdigit() and ":" in tds[2]:
                time_str = tds[2]
                vessel = tds[3]
                route = tds[5] if tds[5] else tds[4]
                results.append({
                    "port": "인천",
                    "vessel": vessel,
                    "callSign": "-",
                    "station": route,
                    "time": f"{today_md} {time_str}"
                })
    except Exception as e:
        print("인천 수집 오류:", e)
    return results

def fetch_daesan():
    results = []
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        res = requests.get("http://ds-pilot.co.kr", headers=HEADERS, timeout=15)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        for tr in soup.select("table tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(tds) >= 5:
                # 시간(HH:MM)이 포함된 행 탐색
                time_idx = next((i for i, v in enumerate(tds) if ":" in v and len(v) == 5), -1)
                if time_idx != -1 and len(tds) > time_idx + 2:
                    results.append({
                        "port": "대산",
                        "vessel": tds[time_idx + 1],
                        "callSign": "-",
                        "station": tds[time_idx + 2],
                        "time": f"{today_md} {tds[time_idx]}"
                    })
    except Exception as e:
        print("대산 수집 오류:", e)
    return results

def main():
    all_data = []
    all_data.extend(fetch_pyeongtaek())
    time.sleep(2)
    all_data.extend(fetch_incheon())
    time.sleep(2)
    all_data.extend(fetch_daesan())

    print(f"총 {len(all_data)}건 수집 완료")

    output = {
        "updatedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "schedules": all_data
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
