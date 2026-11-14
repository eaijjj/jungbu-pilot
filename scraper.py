import json
import re
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
            # 평택: 일자(MM-DD)와 시간(HH:MM) 패턴이 포함된 행 찾기
            if len(tds) >= 10:
                date_idx = next((i for i, v in enumerate(tds) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                time_idx = next((i for i, v in enumerate(tds) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if date_idx != -1 and time_idx != -1 and len(tds) > time_idx + 4:
                    # 긴특 칸이 비어있거나 글자가 있을 수 있으므로 선명 위치 보정
                    vessel = tds[time_idx + 2]
                    from_pt = tds[time_idx + 3]
                    to_pt = tds[time_idx + 4]
                    call_sign = tds[-1] if re.match(r"^[A-Z0-9]{4,7}$", tds[-1]) else "-"
                    results.append({
                        "port": "평택",
                        "vessel": vessel,
                        "callSign": call_sign,
                        "station": f"{from_pt} → {to_pt}",
                        "time": f"{tds[date_idx]} {tds[time_idx]}"
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
            # 인천: 첫 칸이 숫자(No)이고 시간(HH:MM)이 포함된 행 찾기
            if len(tds) >= 6 and tds[0].isdigit():
                time_idx = next((i for i, v in enumerate(tds) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if time_idx != -1 and len(tds) > time_idx + 2:
                    vessel = tds[time_idx + 1]
                    # 갑문 칸 유무에 따라 도선구간(" - " 포함) 찾기
                    route = next((v for v in tds[time_idx+2:time_idx+5] if "-" in v), tds[time_idx + 2])
                    results.append({
                        "port": "인천",
                        "vessel": vessel,
                        "callSign": "-",
                        "station": route,
                        "time": f"{today_md} {tds[time_idx]}"
                    })
    except Exception as e:
        print("인천 수집 오류:", e)
    return results

def fetch_daesan():
    results = []
    today_str = datetime.now(KST).strftime("%Y/%m/%d")
    today_md = datetime.now(KST).strftime("%m-%d")
    try:
        # 대산은 날짜 파라미터를 함께 요청
        res = requests.post(
            "http://ds-pilot.co.kr",
            data={"search_date": today_str},
            headers=HEADERS,
            timeout=15
        )
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        for tr in soup.select("table tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(tds) >= 5:
                time_idx = next((i for i, v in enumerate(tds) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if time_idx != -1 and len(tds) > time_idx + 2:
                    # 조석표(시각/조고 2칸짜리 반복) 제외
                    if not tds[time_idx + 1].isdigit():
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
