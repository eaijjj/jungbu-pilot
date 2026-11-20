import json
import re
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

KST = timezone(timedelta(hours=9))


def pick(cells, i, default="-"):
    if 0 <= i < len(cells) and cells[i]:
        return cells[i]
    return default


def fmt_num(v):
    digits = str(v).replace(",", "").strip()
    if digits.isdigit():
        return f"{int(digits):,}"
    return v if v else "-"


def load_previous():
    try:
        with open("data.json", encoding="utf-8") as f:
            return json.load(f).get("schedules", [])
    except Exception:
        return []


def scrape_all():
    pt_rows = []
    ic_rows = []
    ds_rows = []
    errors = {}
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
                                pt_rows.append({
                                    "port": "평택",
                                    "vessel": vessel,
                                    "callSign": call_sign,
                                    "station": f"{from_pt} → {to_pt}",
                                    "time": f"{cells[date_idx]} {cells[time_idx]}"
                                })
            print(f"평택 수집: {len(pt_rows)}건")
            if len(pt_rows) == 0:
                errors["평택"] = "수집 0건"
        except Exception as e:
            print("평택 오류:", e)
            errors["평택"] = str(e)[:80]

        # 2. 인천항도선사회
        # 표 순서: No(0) 도선사(1) 시간(2) 선명(3) 갑문(4) 도선구간(5) 접안(6) 톤수(7) 홀수(8) 대리점(9)
        try:
            page.goto("http://incheonpilot.com", timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            page.evaluate("location.href = '/pilot/pilot04_01.asp'")
            page.wait_for_timeout(3000)

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
                                ic_rows.append({
                                    "port": "인천",
                                    "vessel": vessel,
                                    "callSign": "-",
                                    "station": route,
                                    "time": f"{today_md} {cells[2]}",
                                    "pilot": pilot,
                                    "agent": pick(cells, 9),
                                    "tonnage": fmt_num(pick(cells, 7))
                                })
            print(f"인천 수집: {len(ic_rows)}건")
            if len(ic_rows) == 0:
                errors["인천"] = "수집 0건"
        except Exception as e:
            print("인천 오류:", e)
            errors["인천"] = str(e)[:80]

        # 3. 대산항도선사회 (오늘 + 내일, 분류가 취소인 건 제외, 통과선박 감지)
        ds_cancel = 0
        ds_fail = ""
        for day_add in (0, 1):
            try:
                d = datetime.now(KST) + timedelta(days=day_add)
                ds_url = "http://www.ds-pilot.co.kr/forecast/status?DT_S=" + d.strftime("%Y%%2F%m%%2F%d")
                page.goto(ds_url, timeout=25000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

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
                            ds_cancel += 1
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

                        # 통과선박: 줄 전체 글자 + 입력칸에 들어 있는 비고 글자에서 찾기
                        row_text = " ".join(cells)
                        try:
                            row_text += " " + r.evaluate(
                                "el => Array.from(el.querySelectorAll('input,textarea,select')).map(x => x.value).join(' ')"
                            )
                        except Exception:
                            pass
                        is_transit = "통과선박" in row_text

                        ds_rows.append({
                            "port": "대산",
                            "vessel": vessel,
                            "callSign": call_sign,
                            "station": f"{from_pt} → {to_pt}",
                            "time": f"{md} {cells[time_idx]}",
                            "pilot": pilot or "-",
                            "agent": agent,
                            "tonnage": tonnage,
                            "transit": is_transit
                        })
            except Exception as e:
                print("대산 오류:", e)
                ds_fail = str(e)[:80]
        print(f"대산 수집: {len(ds_rows)}건 (취소 제외: {ds_cancel}건)")
        if ds_fail:
            errors["대산"] = ds_fail
        elif len(ds_rows) == 0:
            errors["대산"] = "수집 0건"

        browser.close()

    # 인천: 시간이 거꾸로 가면(23:30 → 00:30) 다음날로 처리
    day_offset = 0
    prev_hm = ""
    for item in ic_rows:
        hm = item["time"].split(" ")[1]
        if prev_hm and hm < prev_hm:
            day_offset += 1
        prev_hm = hm
        if day_offset:
            nd = datetime.now(KST) + timedelta(days=day_offset)
            item["time"] = nd.strftime("%m-%d") + " " + hm

    # 수집에 실패한 항구는 직전 정상 데이터를 그대로 사용
    prev_rows = load_previous()
    all_data = []
    for port, rows in (("평택", pt_rows), ("인천", ic_rows), ("대산", ds_rows)):
        if port in errors:
            old = [x for x in prev_rows if x.get("port") == port]
            if old:
                rows = old
        all_data.extend(rows)

    # 같은 항구, 같은 선박, 같은 시간이 두 번 나오면 하나로 합치기 (콜사인이 있는 쪽을 남김)
    merged = {}
    for item in all_data:
        key = (item["port"], item["vessel"], item["time"])
        if key not in merged or (merged[key]["callSign"] == "-" and item["callSign"] != "-"):
            merged[key] = item
    all_data = list(merged.values())

    print(f"총 수집 건수: {len(all_data)}건")
    if errors:
        print("오류 항구:", errors)

    output = {
        "updatedAt": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "schedules": all_data,
        "errors": errors
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    scrape_all()
