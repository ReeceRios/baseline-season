"""Self-check. Run: pip install playwright && python test.py  (needs Chrome)."""
import datetime, http.server, json, pathlib, sys, threading
from playwright.sync_api import sync_playwright

root = pathlib.Path(__file__).resolve().parent
handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(root), **k)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}/index.html"
shots = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None

def open_at(browser, when, width=390, state=None, intro=True):
    ctx = browser.new_context(viewport={"width": width, "height": 844}, device_scale_factor=2)
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.clock.set_fixed_time(datetime.datetime.fromisoformat(when))
    if intro: page.add_init_script("sessionStorage.setItem('bs-intro', 1)")
    if state:
        page.add_init_script(f"localStorage.setItem('baseline-season-v2', {json.dumps(json.dumps(state))})")
    page.goto(url)
    page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    return page

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    # Before the season: shows week 1 and a countdown
    p = open_at(b, "2026-11-14T13:00:00")
    assert "In 2 days" in p.inner_text("#phase"), p.inner_text("#phase")
    assert "Week 1: Mon 16 Nov – Sun 22 Nov" in p.inner_text("#weekTitle"), p.inner_text("#weekTitle")
    assert "Pre-season · Sat 14 Nov" in p.inner_text("#today") and p.locator("#today .tick").count() == 1 and "Vert test" not in p.inner_text("#today")
    p.locator("#today .tick").click(); assert "Done" in p.inner_text("#today .donebtn") and "0 of 84 days" in p.inner_text("#phase")
    # Week 2, a Monday lifting day: loads from baseline, 5K test flagged
    p = open_at(b, "2026-11-23T08:00:00")
    assert "Week 2 of 12" in p.inner_text("#sub")
    assert "Mon 23 Nov – Sun 29 Nov" in p.inner_text("#weekTitle")
    t = p.inner_text("#today")
    assert "Full A" in t and "135–158" in t and "5K time trial" in t, t
    # Check-off is per date and survives a reload
    p.click("#today [data-done]"); p.reload(); p.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
    assert "1 of 7" in p.inner_text("#donecount")
    # A tested max moves current, keeps baseline, recomputes loads
    p.select_option("#logType", "lift"); p.select_option("#logLift", "squat_lb")
    p.fill("#logWeight", "235"); p.check("#logMax"); p.click("#logForm button")
    assert "235 lb" in p.inner_text("#lifts") and "Baseline 225 lb · +10 lb" in p.inner_text("#lifts")
    assert "141–165" in p.inner_text("#today") and "135 · 235 · 325 lb" in p.inner_text("#sumLift")
    # Vert and run tests drive the dashboard; bad time is refused
    p.select_option("#logType", "vert"); p.fill("#logFt", "9"); p.fill("#logIn", "9"); p.click("#logForm button")
    assert "9'9\" reach" in p.inner_text("#reach") and "3 in to rim touch" in p.inner_text("#rimgap")
    p.select_option("#logType", "run"); p.fill("#logTime", "24:75"); p.click("#logForm button")
    assert "mm:ss" in p.inner_text("#logMsg") and "Not tested yet" in p.inner_text("#r5K")
    p.fill("#logTime", "24:30"); p.click("#logForm button")
    assert p.inner_text("#r5K").startswith("24:30")
    # Text a user types is escaped
    p.select_option("#logType", "workout"); p.fill("#logLabel", "<img src=x onerror=alert(1)>"); p.click("#logForm button")
    assert p.locator("#history img").count() == 0
    # Backup round trip, and a bad backup changes nothing
    p.click("#bkCopy"); backup = p.input_value("#bk")
    assert len(json.loads(backup)["logs"]) == 4
    p.fill("#bk", "{nope"); p.click("#bkRestore"); assert "Nothing changed" in p.inner_text("#bkMsg")
    assert p.locator("#history li").count() == 4
    if shots: p.screenshot(path=str(shots / "week2-390.png"), full_page=True)
    # Delete needs two taps
    d = p.locator("#history .del").first; d.click(); assert p.locator("#history li").count() == 4
    p.locator("#history .del").first.click(); assert p.locator("#history li").count() == 3
    # Restore on a fresh phone; week 12 and after the season
    p = open_at(b, "2027-02-05T08:00:00", state=json.loads(backup))
    assert "Week 12 of 12" in p.inner_text("#sub") and "Retest week" in p.inner_text("#today")
    assert "0 of 7" in p.inner_text("#donecount") and p.locator("#history li").count() == 4
    p = open_at(b, "2027-02-08T08:00:00")
    assert "Week 13" in p.inner_text("#sub") and "Build phase" in p.inner_text("#phase")
    # Tap-to-complete steps: ticking every step marks the day done; calendar shows it
    p = open_at(b, "2026-11-24T08:00:00")
    assert p.locator("#today .tick").count() == 2 and "0 of 7" in p.inner_text("#donecount")
    p.locator("#today .tick").nth(0).click(); assert "1 of 2 steps" in p.inner_text("#today")
    p.locator("#today .tick").nth(1).click(); assert "1 of 7" in p.inner_text("#donecount")
    p.reload(); assert p.locator("#today .tick.is").count() == 2
    p.click("#tabs [data-tab=week]")
    assert p.locator("#cal button").count() == 84 and p.locator("#cal button.is").count() == 1
    p.click("#cal [data-cal='2026-11-24']"); assert "Tue 24 Nov" in p.inner_text("#calDetail") and "Done" in p.inner_text("#calDetail")
    # Rest timer counts down on the real clock, so it stays right after the screen sleeps
    ctx = b.new_context(); p = ctx.new_page(); p.on("pageerror", lambda e: errors.append(str(e)))
    p.clock.install(time=datetime.datetime.fromisoformat("2026-11-24T08:00:00")); p.goto(url); p.click("#introGo"); p.click("#quoteGo"); assert p.locator("details").first.get_attribute("open") is not None
    p.click("[data-rest='90']"); assert p.inner_text("#restOut") == "1:30"
    p.clock.fast_forward(60000); assert p.inner_text("#restOut") == "0:30", p.inner_text("#restOut")
    p.clock.fast_forward(31000); assert p.inner_text("#restOut") == "0:00" and "Rest over" in p.inner_text("#restMsg")
    p.click("[data-rest='60']"); p.click("[data-rest='0']"); assert p.inner_text("#restOut") == "0:00"
    # Opening screen shows once per launch, names today's session, and blocks the page until dismissed
    p = open_at(b, "2026-11-23T08:00:00", intro=False)
    assert p.locator("#intro").is_visible() and "Week 2 · Mon 23 Nov · Full A" in p.inner_text("#introDay")
    assert p.evaluate("document.querySelector('body>.wrap').inert") and p.evaluate("document.activeElement.id") == "introGo"
    assert "1% better every day" in p.inner_text("#intro")
    assert p.locator("#frames .f").count() == 8 and "NaN" not in p.inner_html("#frames")
    p.click("#introGo"); assert not p.locator("#intro").is_visible() and p.locator("#quote").is_visible()
    assert "try again" in p.inner_text("#quoteText").lower() and p.evaluate("document.querySelector('body>.wrap').inert")
    p.click("#quoteGo"); assert not p.locator("#quote").is_visible() and not p.evaluate("document.querySelector('body>.wrap').inert")
    p.reload(); assert not p.locator("#intro").is_visible()
    assert "0 of 84 days" in p.inner_text("#phase") and p.locator("#season rect").count() == 84
    # Collapsed by default: the dashboard is short, each row carries its number, a tap on text inside a step still ticks it
    p = open_at(b, "2026-11-23T08:00:00", state=json.loads(backup)); p.evaluate("document.querySelectorAll('#dash details').forEach((d, i) => d.open = i === 0)")
    assert p.evaluate("document.documentElement.scrollHeight") < 2700, p.evaluate("document.documentElement.scrollHeight")
    assert "9'9\"" in p.inner_text("#sumDunk") and "5K 24:30" in p.inner_text("#sumRun") and not p.locator("#logForm").is_visible()
    p.locator("#today .tick b").first.click(); assert p.locator("#today .tick.is").count() == 1
    p.click("#tabs [data-tab=workouts]"); assert p.locator("#workouts li b").first.inner_text() == "Tendon prep" and "@garagestrength" in p.locator("#workouts li .src").first.inner_text()
    # Section tiles, previous / next buttons and a sideways swipe all move between sections
    p = open_at(b, "2026-11-23T08:00:00")
    p.wait_for_function("[...document.querySelectorAll('#tiles img')].every(i => i.complete)")
    assert p.locator("#tiles .tile img").count() == 4 and p.evaluate("[...document.querySelectorAll('#tiles img')].every(i => i.naturalWidth === 360)")
    p.click("#tiles [data-go=mob]")
    assert p.locator("#workouts").is_visible() and p.locator("#workouts details[open]").count() == 1 and p.locator("#workouts details[open] .p-mob").count() == 1
    p.click("#workouts .pager [data-nav=flows]"); assert p.locator("#flows").is_visible() and p.locator("#tabs .on").inner_text().strip() == "Flows"
    swipe = "(dx) => { const mk = (type, x) => document.body.dispatchEvent(new TouchEvent(type, {bubbles: true, changedTouches: [new Touch({identifier: 1, target: document.body, clientX: x, clientY: 400})]})); mk('touchstart', 200); mk('touchend', 200 + dx); }"
    p.evaluate(swipe, -120); assert p.locator("#road").is_visible()
    p.evaluate(swipe, -120); assert p.locator("#road").is_visible()
    p.evaluate(swipe, 120); assert p.locator("#flows").is_visible()
    p.evaluate(swipe, 30); assert p.locator("#flows").is_visible()
    # Nothing scrolls sideways on a small phone, on any tab
    p = open_at(b, "2026-11-23T08:00:00", width=320, state=json.loads(backup))
    for tab in ["dash", "week", "workouts", "flows", "road"]:
        p.click(f"#tabs [data-tab={tab}]")
        assert p.evaluate("document.documentElement.scrollWidth") <= 320, tab
        if shots: p.screenshot(path=str(shots / f"{tab}-320.png"), full_page=True)
    b.close()
assert not errors, errors
print("ok")
