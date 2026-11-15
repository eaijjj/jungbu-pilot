from playwright.sync_api import sync_playwright

TARGETS = [
    ("인천", "http://incheonpilot.com", "/pilot/pilot04_01.asp"),
    ("대산", "http://www.ds-pilot.co.kr/forecast/status", None),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    for name, url, path in TARGETS:
        print("=" * 60)
        print(name, "접속:", url)
        try:
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)
            if path:
                page.evaluate(f"location.href = '{path}'")
            page.wait_for_timeout(4000)

            print("현재 URL:", page.url)
            print("프레임 수:", len(page.frames))
            for fi, frame in enumerate(page.frames):
                rows = frame.locator("tr").all()
                print(f"--- 프레임 {fi}: {frame.url} (tr {len(rows)}개)")
                shown = 0
                for r in rows:
                    cells = [c.inner_text().strip() for c in r.locator("td").all()]
                    if len(cells) >= 4:
                        print(cells)
                        shown += 1
                        if shown >= 15:
                            break

            print("--- 메뉴 링크(도선 관련) ---")
            for a in page.locator("a").all()[:60]:
                t = a.inner_text().strip()
                if "도선" in t or "예보" in t or "스케줄" in t:
                    print(t, "->", a.get_attribute("href"))
        except Exception as e:
            print("오류:", e)

    browser.close()
