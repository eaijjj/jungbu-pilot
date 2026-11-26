import json
import re
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))

# 연속 몇 번 실패해야 화면에 "원본 사이트 오류" 경고를 띄울지 (수집은 30분마다)
SHOW_ERROR_AFTER = 2
# 항구별 최대 시도 횟수
MAX_TRIES = 3

TIDE_FILE = "tide-daesan.json"

STATS = {"cancel": 0}
TIDE = {}  # {"2026-11-22": {"02:02": 640, ...}}


def pick(cells, i, default="-"):
    if 0 <= i < len(cells) and cells[i]:
        return cells[i]
    return default


def kv(pairs):
    # 값이 비어 있거나 "-" 인 항목은 빼고 [이름, 값] 목록으로 만들기
    return [[k, v] for k, v in pairs if v and v != "-"]


def with_unit(v, unit):
    return f"{v} {unit}" if v and v != "-" else "-"


def fmt_num(v):
    digits = str(v).replace(",", "").strip()
    if digits.isdigit():
        return f"{int(digits):,}"
    return v if v else "-"


def is_phone(v):
    s = str(v).strip()
    if not re.match(r"^[0-9\-\s().]+$", s):
        return False
    d = re.sub(r"[^0-9]", "", s)
    return d.startswith("0") and 9 <= len(d) <= 11


def fmt_tel(v):
    d = re.sub(r"[^0-9]", "", str(v))
    # 서울 02: 9자리 02-000-0000 / 10자리 02-0000-0000
    if d.startswith("02"):
        if len(d) == 10:
            return f"{d[:2]}-{d[2:6]}-{d[6:]}"
        if len(d) == 9:
            return f"{d[:2]}-{d[2:5]}-{d[5:]}"
    # 11자리: 010-0000-0000 처럼 가운데 4자리
    if len(d) == 11:
        return f"{d[:3]}-{d[3:7]}-{d[7:]}"
    # 10자리: 041-000-0000 처럼 가운데 3자리
    if len(d) == 10:
        return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    return str(v).strip()


def load_previous():
    try:
        with open("data.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def wait_for_table(page):
    # 표 칸이 나타날 때까지 최대 10초 기다림 (없어도 계속 진행)
    try:
        page.wait_for_selector("td", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(1500)


def fetch_with_retry(fn, name, page):
    last_err = ""
    for n in range(1, MAX_TRIES + 1):
        try:
            rows = fn(page)
            if rows:
                return rows, ""
            last_err = "수집 0건"
        except Exception as e:
            last_err = str(e)[:80]
        print(f"{name} 시도 {n}/{MAX_TRIES} 실패: {last_err}")
        page.wait_for_timeout(3000)
    return [], last_err


# ---------- 대산항 조석(조고) ----------
# 대산 도선예보 페이지 아래쪽 조석표(날짜 / 항만 / 시각 / 조고)에서 대산항 줄만 모읍니다.
# 날짜와 항만 칸은 여러 줄을 합친 칸이라 첫 줄에만 있어서, 지나온 값을 기억하며 읽습니다.
def collect_tide(page):
    try:
        for frame in page.frames:
            cur_date = ""
            cur_port = ""
            for r in frame.locator("tr").all():
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if not cells or len(cells) > 4:
                    continue
                for c in cells:
                    if re.match(r"^\d{2}/\d{2}/\d{2}$", c):
                        cur_date = "20" + c.replace("/", "-")
                    elif c.endswith("항") and len(c) <= 6:
                        cur_port = c
                if (
                    len(cells) >= 2
                    and re.match(r"^\d{2}:\d{2}$", cells[-2])
                    and re.fullmatch(r"-?[0-9]{1,4}", cells[-1])
                    and cur_port == "대산항"
                    and cur_date
                ):
                    TIDE.setdefault(cur_date, {})[cells[-2]] = int(cells[-1])
    except Exception as e:
        print("조석 수집 오류:", e)


def read_tide_days():
    days = {}
    try:
        with open(TIDE_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return days
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and isinstance(raw.get("days"), list):
        items = raw["days"]
    else:
        items = [raw]
    for it in items:
        try:
            days[it["date"]] = [{"time": p["time"], "h": int(p["h"])} for p in it["points"]]
        except Exception:
            continue
    return days


def save_tide():
    if not TIDE:
        print("조석 수집: 새로 읽은 값 없음 (기존 파일 유지)")
        return
    days = read_tide_days()
    for date, pts in TIDE.items():
        if len(pts) >= 2:
            days[date] = [{"time": t, "h": h} for t, h in sorted(pts.items())]
    yesterday = (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
    days = {k: v for k, v in days.items() if k >= yesterday}
    if not days:
        return
    out = {"port": "대산항", "days": [{"date": k, "points": days[k]} for k in sorted(days)]}
    with open(TIDE_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("조석 저장:", sorted(days.keys()))


# 1. 평택당진도선사회
def scrape_pt(page):
    rows = []
    page.goto("http://ptpilot.co.kr", timeout=40000, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    page.evaluate("location.href = '/forecast/1'")
    wait_for_table(page)

    pt_debug = 0
    for frame in page.frames:
        heads = [h.inner_text().strip() for h in frame.locator("th").all()]
        heads = [h for h in heads if h]
        if heads:
            print("PTHEAD", heads[:40])
        for r in frame.locator("tr").all():
            cells = [c.inner_text().strip() for c in r.locator("td").all()]
            if len(cells) >= 10:
                date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}-\d{2}$", v)), -1)
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if date_idx != -1 and time_idx != -1 and len(cells) > time_idx + 3:
                    if pt_debug < 6:
                        print("PTDEBUG", cells)
                        pt_debug += 1
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


# 2. 인천항도선사회
# 표 순서: No(0) 도선사(1) 시간(2) 선명(3) 갑문(4) 도선구간(5) 접안(6) 톤수(7) 홀수(8) 대리점(9)
def scrape_ic(page):
    rows = []
    today_md = datetime.now(KST).strftime("%m-%d")
    page.goto("http://incheonpilot.com", timeout=40000, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)
    page.evaluate("location.href = '/pilot/pilot04_01.asp'")
    wait_for_table(page)

    for frame in page.frames:
        for r in frame.locator("tr").all():
            cells = [c.inner_text().strip() for c in r.locator("td").all()]
            if len(cells) >= 8:
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if time_idx == 2 and len(cells) > 5:
                    vessel = cells[3]
                    route = next((v for v in cells[4:7] if "-" in v), cells[4])
                    if vessel and vessel != "선명":
                        pilot = cells[1]
                        if pilot in ("", "(0)"):
                            pilot = "-"
                        rows.append({
                            "port": "인천",
                            "vessel": vessel,
                            "callSign": "-",
                            "station": route,
                            "time": f"{today_md} {cells[2]}",
                            "pilot": pilot,
                            "agent": pick(cells, 9),
                            "tonnage": fmt_num(pick(cells, 7))
                        })

    # 시간이 거꾸로 가면(23:30 → 00:30) 다음날로 처리
    day_offset = 0
    prev_hm = ""
    for item in rows:
        hm = item["time"].split(" ")[1]
        if prev_hm and hm < prev_hm:
            day_offset += 1
        prev_hm = hm
        if day_offset:
            nd = datetime.now(KST) + timedelta(days=day_offset)
            item["time"] = nd.strftime("%m-%d") + " " + hm
    return rows


# 3. 대산항도선사회 (오늘 + 내일, 분류가 취소인 건 제외, 통과선박 감지)
# 시간 칸 기준 위치: 도선점 +1,+2 / 콜사인 +3 / 대리점 +4 / 총톤수 +5 / 흘수 +6 / 전장 +8
#                   접안 +23 / 화물(적재, 공선) +24 / 담당자 +26 / 연락처 +27
def scrape_ds(page):
    rows = []
    STATS["cancel"] = 0
    for day_add in (0, 1):
        d = datetime.now(KST) + timedelta(days=day_add)
        ds_url = "http://www.ds-pilot.co.kr/forecast/status?DT_S=" + d.strftime("%Y%%2F%m%%2F%d")
        page.goto(ds_url, timeout=40000, wait_until="domcontentloaded")
        wait_for_table(page)

        # 같은 페이지 아래쪽의 조석표도 함께 읽음 (실패해도 스케줄 수집에는 영향 없음)
        collect_tide(page)

        for frame in page.frames:
            for r in frame.locator("tr").all():
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                if len(cells) < 10:
                    continue
                date_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{4}/\d{2}/\d{2}$", v)), -1)
                time_idx = next((i for i, v in enumerate(cells) if re.match(r"^\d{2}:\d{2}$", v)), -1)
                if date_idx == -1 or time_idx < 4 or len(cells) <= time_idx + 3:
                    continue

                # 분류 칸(날짜 바로 다음 칸)이 취소면 제외
                if cells[date_idx + 1] == "취소" or "취소" in cells:
                    STATS["cancel"] += 1
                    continue

                vessel = cells[time_idx - 1]
                if not vessel:
                    continue

                pilot_a = cells[time_idx - 3]
                pilot_b = cells[time_idx - 2]
                pilot = f"{pilot_a} / {pilot_b}" if pilot_b else pilot_a

                from_pt = cells[time_idx + 1]
                to_pt = cells[time_idx + 2]
                call_sign = cells[time_idx + 3] if re.match(r"^[A-Z0-9]{4,8}$", cells[time_idx + 3]) else "-"
                tonnage = pick(cells, time_idx + 5)
                agent = pick(cells, time_idx + 4)
                md = cells[date_idx][5:].replace("/", "-")

                # 담당자 이름과 연락처 (줄 뒤쪽에서 전화번호 칸을 찾음)
                tel = ""
                contact = ""
                for ti in range(len(cells) - 1, time_idx, -1):
                    if is_phone(cells[ti]):
                        tel = fmt_tel(cells[ti])
                        prev_cell = cells[ti - 1] if ti - 1 > time_idx else ""
                        if prev_cell and not is_phone(prev_cell) and not re.match(r"^[0-9.,\-]+$", prev_cell):
                            contact = prev_cell
                        break
                if not tel and not contact:
                    cand = pick(cells, time_idx + 26)
                    if cand != "-" and not re.match(r"^[A-Z]$", cand):
                        contact = cand

                # 통과선박: 줄 전체 글자 + 입력칸에 들어 있는 비고 글자에서 찾기
                row_text = " ".join(cells)
                try:
                    row_text += " " + r.evaluate(
                        "el => Array.from(el.querySelectorAll('input,textarea,select')).map(x => x.value).join(' ')"
                    )
                except Exception:
                    pass
                is_transit = "통과선박" in row_text

                # 접안은 좌현/우현/무관만, 화물은 적재/공선만 인정
                berth = pick(cells, time_idx + 23)
                if berth not in ("좌현", "우현", "무관"):
                    berth = "-"
                cargo = pick(cells, time_idx + 24)
                if cargo not in ("적재", "공선"):
                    cargo = "-"

                detail = kv([
                    ("흘수", with_unit(pick(cells, time_idx + 6), "m")),
                    ("전장", with_unit(pick(cells, time_idx + 8), "m")),
                    ("접안", berth),
                    ("화물", cargo),
                    ("담당자", contact),
                    ("연락처", tel)
                ])

                rows.append({
                    "port": "대산",
                    "vessel": vessel,
                    "callSign": call_sign,
                    "station": f"{from_pt} → {to_pt}",
                    "time": f"{md} {cells[time_idx]}",
                    "pilot": pilot or "-",
                    "agent": agent,
                    "tonnage": tonnage,
                    "transit": is_transit,
                    "detail": detail
                })
    return rows


def scrape_all():
    prev = load_previous()
    prev_rows = prev.get("schedules", [])
    prev_streak = prev.get("failStreak", {})

    results = {}
    fail_msg = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()

        for port, fn in (("평택", scrape_pt), ("인천", scrape_ic), ("대산", scrape_ds)):
            rows, err = fetch_with_retry(fn, port, page)
            results[port] = rows
            if err:
                fail_msg[port] = err
            print(f"{port} 수집: {len(rows)}건" + (f" (취소 제외: {STATS['cancel']}건)" if port == "대산" else ""))

        browser.close()

    # 조석(조고) 파일 저장 (읽은 값이 있을 때만, 기존 날짜는 합쳐서 유지)
    try:
        save_tide()
    except Exception as e:
        print("조석 저장 오류:", e)

    # 실패한 항구는 직전 정상 데이터를 그대로 쓰고, 연속 실패 횟수를 기록
    streak = {}
    errors = {}
    all_data = []
    for port in ("평택", "인천", "대산"):
        rows = results.get(port, [])
        if port in fail_msg:
            streak[port] = int(prev_streak.get(port, 0)) + 1
            old = [x for x in prev_rows if x.get("port") == port]
            if old:
                rows = old
            if streak[port] >= SHOW_ERROR_AFTER:
                errors[port] = fail_msg[port]
        else:
            streak[port] = 0
        all_data.extend(rows)

    # 같은 항구, 같은 선박, 같은 시간이 두 번 나오면 하나로 합치기 (콜사인이 있는 쪽을 남김)
    merged = {}
    for item in all_data:
        key = (item["port"], item["vessel"], item["time"])
        if key not in merged or (merged[key]["callSign"] == "-" and item["callSign"] != "-"):
            merged[key] = item
    all_data = list(merged.values())

    print(f"총 수집 건수: {len(all_data)}건")
    if fail_msg:
        print("이번 실패:", fail_msg, "/ 연속 실패:", streak)

    output = {
        "updatedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "schedules": all_data,
        "errors": errors,
        "failStreak": streak
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    scrape_all()
