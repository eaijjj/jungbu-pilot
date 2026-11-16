"""서해 중부(인천·평택·대산) 도선 스케줄 수집기.

원본 사이트 중 하나라도 접속·파싱에 실패하면(예외 또는 0건) 그 항구는 직전 정상
데이터를 그대로 유지하고, data.json 의 "errors" 에 실패 사유를 남긴다.
웹 화면(index.html)은 errors 가 비어 있지 않으면 경고 배너를 띄운다.
"""

import json
import re
import time
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))
DATA_FILE = "data.json"
PORTS = ["평택", "인천", "대산"]

ERR_CONN = "원본 사이트 접속 오류 (타임아웃·연결 실패)"
ERR_PARSE = "원본 사이트 응답 오류 (페이지 구조 변경·로딩 중단)"
ERR_EMPTY = "원본 사이트 응답 오류 (자료 없음)"

ATTEMPTS = 2          # 한 항구당 시도 횟수
RETRY_WAIT = 5        # 재시도 전 대기(초)


def classify_error(e):
    """예외 메시지로 접속 실패와 응답(파싱) 실패를 구분한다."""
    msg = str(e)
    conn_signs = ("Timeout", "timeout", "net::", "ERR_", "ECONN", "getaddrinfo", "ENOTFOUND")
    return ERR_CONN if any(s in msg for s in conn_signs) else ERR_PARSE


# ---------------------------------------------------------------- 수집 함수
def fetch_pyeongtaek(page, today_md):
    """평택당진도선사회 (http://ptpilot.co.kr/forecast/1)"""
    page.goto("http://ptpilot.co.kr", timeout=25000, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    page.evaluate("location.href = '/forecast/1'")
    page.wait_for_timeout(3000)

    rows = []
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
                        rows.append({
                            "port": "평택",
                            "vessel": vessel,
                            "callSign": call_sign,
                            "station": f"{from_pt} → {to_pt}",
                            "time": f"{cells[date_idx]} {cells[time_idx]}"
                        })
    return rows


def fetch_incheon(page, today_md):
    """인천항도선사회 (http://incheonpilot.com/pilot/pilot04_01.asp)"""
    page.goto("http://incheonpilot.com", timeout=25000, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    page.evaluate("location.href = '/pilot/pilot04_01.asp'")
    page.wait_for_timeout(3000)

    rows = []
    for frame in page.frames:
        for r in frame.locator("tr").all():
            cells = [c.inner_text().strip() for c in r.locator("td").all()]
            if len(cells) >= 8:
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if time_idx == 2 and len(cells) > 5:
                    vessel = cells[3]
                    route = next((v for v in cells[4:7] if "-" in v), cells[4])
                    if vessel and vessel != "선명":
                        rows.append({
                            "port": "인천",
                            "vessel": vessel,
                            "callSign": "-",
                            "station": route,
                            "time": f"{today_md} {cells[2]}"
                        })

    # 인천: 시간이 거꾸로 가면(23:30 → 00:30) 다음날로 처리
    day_offset = 0
    prev = ""
    for item in rows:
        hm = item["time"].split(" ")[1]
        if prev and hm < prev:
            day_offset += 1
        prev = hm
        if day_offset:
            nd = datetime.now(KST) + timedelta(days=day_offset)
            item["time"] = nd.strftime("%m-%d") + " " + hm
    return rows


def fetch_daesan(page, today_md):
    """대산항도선사회 (오늘 + 내일)"""
    rows = []
    last_err = None
    for day_add in (0, 1):
        d = datetime.now(KST) + timedelta(days=day_add)
        ds_url = "http://www.ds-pilot.co.kr/forecast/status?DT_S=" + d.strftime("%Y%%2F%m%%2F%d")
        try:
            page.goto(ds_url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            for frame in page.frames:
                for r in frame.locator("tr").all():
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) < 10:
                        continue
                    date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{4}/\d{2}/\d{2}$", v)), -1)
                    time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                    if date_idx == -1 or time_idx == -1 or len(cells) <= time_idx + 3:
                        continue

                    vessel = cells[time_idx - 1]
                    from_pt = cells[time_idx + 1]
                    to_pt = cells[time_idx + 2]
                    call_sign = cells[time_idx + 3] if re.match(r"^[A-Z0-9]{4,8}$", cells[time_idx + 3]) else "-"
                    md = cells[date_idx][5:].replace("/", "-")

                    if vessel:
                        rows.append({
                            "port": "대산",
                            "vessel": vessel,
                            "callSign": call_sign,
                            "station": f"{from_pt} → {to_pt}",
                            "time": f"{md} {cells[time_idx]}"
                        })
        except Exception as e:
            last_err = e
            print(f"대산 {day_add}일차 오류:", e)

    if not rows and last_err:
        raise last_err
    return rows


SCRAPERS = {
    "평택": fetch_pyeongtaek,
    "인천": fetch_incheon,
    "대산": fetch_daesan,
}


# ---------------------------------------------------------------- 병합/저장
def load_previous():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            prev = json.load(f)
        return prev if isinstance(prev, dict) else {}
    except FileNotFoundError:
        print(f"{DATA_FILE} 없음 → 이전 데이터 없이 진행")
        return {}
    except Exception as e:
        print(f"{DATA_FILE} 읽기 실패 → 이전 데이터 없이 진행:", e)
        return {}


def build_output(prev, fetched, errors, now_str):
    """실패한 항구는 직전 정상 데이터를 유지하고 errors 에 사유를 남긴다."""
    prev_schedules = prev.get("schedules") if isinstance(prev.get("schedules"), list) else []
    schedules = []

    for port in PORTS:
        if port in fetched:
            schedules.extend(fetched[port])
            continue
        kept = [s for s in prev_schedules if isinstance(s, dict) and s.get("port") == port]
        schedules.extend(kept)
        print(f"{port}: 실패 → 이전 데이터 {len(kept)}건 유지 ({errors.get(port, '')})")

    # 알려진 항구 외 옛 항목은 손대지 않고 그대로 보존
    for s in prev_schedules:
        if isinstance(s, dict) and s.get("port") not in PORTS:
            schedules.append(s)

    # 모든 항구가 실패한 경우엔 데이터가 전부 이전 값이므로 updatedAt 을 앞당기지 않는다
    updated_at = now_str if fetched else (prev.get("updatedAt") or now_str)

    return {
        "updatedAt": updated_at,
        "errors": errors,
        "schedules": schedules,
    }


# ---------------------------------------------------------------- 메인
def scrape_all():
    today_md = datetime.now(KST).strftime("%m-%d")
    fetched = {}
    errors = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )

        for port in PORTS:
            rows = None
            last_err = None

            for attempt in range(1, ATTEMPTS + 1):
                page = context.new_page()
                try:
                    got = SCRAPERS[port](page, today_md)
                    if got:
                        print(f"{port} 수집: {len(got)}건 ({attempt}차 시도)")
                        rows = got
                        break
                    last_err = ERR_EMPTY
                    print(f"{port} 0건 ({attempt}차 시도)")
                except Exception as e:
                    last_err = classify_error(e)
                    print(f"{port} 오류 ({attempt}차 시도):", e)
                finally:
                    page.close()

                if attempt < ATTEMPTS:
                    time.sleep(RETRY_WAIT)

            if rows is None:
                errors[port] = last_err or ERR_EMPTY
            else:
                fetched[port] = rows

        browser.close()

    prev = load_previous()
    output = build_output(prev, fetched, errors, datetime.now(KST).strftime("%Y-%m-%d %H:%M"))

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"총 수집 건수: {len(output['schedules'])}건")
    if errors:
        for port, msg in errors.items():
            print(f"[원본 사이트 오류] {port}: {msg}")
    else:
        print("모든 항구 정상 수집")


if __name__ == "__main__":
    scrape_all()
