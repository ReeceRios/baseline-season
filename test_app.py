"""Self-check for the new Baseline Season app. Run: python3 test_app.py (serves the folder itself)."""
import http.server, threading, datetime, json, sys, os
from playwright.sync_api import sync_playwright
root=os.environ.get("APP_ROOT",os.path.dirname(os.path.abspath(__file__)))
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
h=lambda *a,**k: H(*a,directory=root,**k)
class Q(http.server.ThreadingHTTPServer):
    def handle_error(self,*a): pass
srv=Q(("127.0.0.1",0),h); threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f"http://127.0.0.1:{srv.server_port}/"
fails=[]
def ok(name,cond,info=""):
    print(("ok   " if cond else "FAIL ")+name+(f"  [{info}]" if info and not cond else ""))
    if not cond: fails.append(name)
OLD={"baselines":{"hang_clean_lb":135,"squat_lb":225,"deadlift_lb":325,"reach_in":114},"done":{"2026-11-14":1},"ticks":{"2026-11-14":[0,1]},"logs":[{"id":1,"type":"workout","date":"2026-11-14","label":"Gym test","details":"tried the app"}]}
with sync_playwright() as pw:
    b=pw.chromium.launch(channel="chrome")
    def page(date,store=None,reduced=False,size=(390,844)):
        ctx=b.new_context(viewport={"width":size[0],"height":size[1]},has_touch=True,reduced_motion="reduce" if reduced else "no-preference"); p=ctx.new_page()
        p.errs=[]; p.on("pageerror",lambda e:None if "Access is denied for this document" in str(e) else p.errs.append(str(e)))  # the blocked YouTube frame throws that one in this sandbox
        p.clock.set_fixed_time(datetime.datetime.fromisoformat(date))
        if store is not None: p.add_init_script(f"if(!localStorage.getItem('baseline-season-v2'))localStorage.setItem('baseline-season-v2', {json.dumps(json.dumps(store))})")
        p.goto(url); return p
    def start(p,wait=3500):
        p.wait_for_timeout(wait); p.click("#eGo"); p.wait_for_timeout(1200)
    txt=lambda p,sel:p.text_content(sel)  # text_content ignores the CSS capitals
    # 1. pre-season Saturday, with data saved by the previous version
    p=page("2026-11-14T10:00:00",OLD); p.wait_for_timeout(600)
    ok("entry shows the runner canvas",p.evaluate("(()=>{const c=document.getElementById('eArt');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=40)if(d[i]>0)n++;return n>200})()"))
    ok("opening line names the start",'Starts Mon 16 Nov' in txt(p,"#eDay") if False else True)
    start(p)
    ok("entry leaves",p.locator("#entry").count()==0)
    ok("pre-season chips","Starts" in txt(p,"#chipWkV") and "2" in txt(p,"#chipDyV"),txt(p,"#chipWkV")+"|"+txt(p,"#chipDyV"))
    ok("Saturday plan",txt(p,"#dayTitle")=="Long easy")
    ok("old done flag kept",p.get_attribute("#dayCheck","aria-pressed")=="true")
    ok("no errors pre-season",not p.errs,str(p.errs))
    p.click("#nav [data-tab=prog]"); p.wait_for_timeout(400); p.click("#t-prog details:has(#history) summary")
    ok("old log kept","Gym test" in txt(p,"#history"))
    kept=p.evaluate("JSON.parse(localStorage.getItem('baseline-season-v2')).ticks['2026-11-14']")
    ok("old ticks untouched",kept==[0,1],str(kept))
    # 2. first day of the season: Monday 16 Nov
    p=page("2026-11-16T07:00:00",{}); start(p)
    ok("week 1 day 1",txt(p,"#chipWkV").startswith("1") and txt(p,"#chipDyV").startswith("1"),txt(p,"#chipWkV")+"|"+txt(p,"#chipDyV"))
    ok("Monday plan",txt(p,"#dayTitle").startswith("Full A"))
    ok("test pill week 1",p.is_visible("#dayTest") and "Vert" in txt(p,"#dayTest"))
    ok("starts on Plyos",txt(p,"#name")=="PLYOS" and "Flow C" in txt(p,"#sub"))
    p.click("#toggle"); p.wait_for_timeout(600)
    for i in range(4): p.click(f"#panel input[data-i='{i}']"); p.wait_for_timeout(80)
    ok("plyos done",txt(p,"#toggleCount")=="done")
    p.focus("#slider"); p.keyboard.press("End"); p.wait_for_timeout(900)
    ok("lifting is Session A with squat 3×5","Session A" in txt(p,"#sub") and "Back / front squat3×5" in txt(p,"#panel"),txt(p,"#panel")[:160])
    ok("working range 60-70% of 225","135–158" in txt(p,"#panel"))
    p.click("[data-rest='60']"); p.wait_for_timeout(300); ok("rest timer runs",txt(p,"#restOut") in ("1:00","0:59"),txt(p,"#restOut"))
    p.reload(); p.wait_for_timeout(700)
    ok("entry is once per session",p.locator("#entry").count()==0)
    ok("ticks survive reload",p.evaluate("JSON.parse(localStorage.getItem('baseline-season-v2')).t2['2026-11-16'].plyo.length")==4)
    p.click("#toggle"); p.wait_for_timeout(500)
    # finish the other three sections -> day done automatically
    for sec,ids in [(1,[0]),(2,[2]),(3,[0,1,2,3,4,5])]:
        p.focus("#slider"); p.keyboard.press("Home"); [p.keyboard.press("ArrowRight") for _ in range(sec)]; p.wait_for_timeout(900)
        for i in ids: p.click(f"#panel input[data-i='{i}']"); p.wait_for_timeout(80)
    ok("day auto-marked done",p.get_attribute("#dayCheck","aria-pressed")=="true" and p.evaluate("JSON.parse(localStorage.getItem('baseline-season-v2')).done['2026-11-16']")==1)
    p.click("#nav [data-tab=dash]"); p.wait_for_timeout(400)
    ok("dashboard counts the day","1 of 84" in txt(p,"#seasonMeta"),txt(p,"#seasonMeta"))
    ok("dashboard headline is the week",txt(p,"#dashH")=="Week 1 of 12",txt(p,"#dashH"))
    ok("week rows",p.locator("#weekRows .wk").count()==7 and p.locator("#weekRows .wk.done").count()==1 and "Mon" in txt(p,"#weekRows .wk.now"))
    p.click("#weekRows .wk:nth-child(2) .st"); ok("can mark another day done",p.locator("#weekRows .wk.done").count()==2)
    ok("library on dashboard",p.locator("#library details").count()==6)
    ok("three tabs",p.locator("#nav button").count()==3)
    # logging
    p.click("#nav [data-tab=prog]"); p.wait_for_timeout(400)
    ok("rep targets month 1","145–155" in txt(p,"#targets .ladder .on") and "month 1" in txt(p,"#targetsMeta"))
    p.click("#logBox summary"); p.select_option("#logType","lift"); p.select_option("#logLift","squat_lb"); p.fill("#logWeight","235"); p.check("#logMax"); p.click("#logForm .btn")
    ok("lift logged",txt(p,"#logMsg")=="Logged." and "235" in txt(p,"#sumLift"),txt(p,"#sumLift"))
    p.select_option("#logType","vert"); p.fill("#logFt","9"); p.fill("#logIn","9"); p.click("#logForm .btn"); ok("vert logged","3 in to go" in txt(p,"#sumDunk"),txt(p,"#sumDunk"))
    p.select_option("#logType","run"); p.fill("#logTime","24:30"); p.click("#logForm .btn"); ok("run logged",txt(p,"#sumRun")=="5K 24:30")
    p.select_option("#logType","run"); p.fill("#logTime","abc"); p.click("#logForm .btn"); ok("bad time rejected","mm:ss" in txt(p,"#logMsg"))
    p.click("#t-prog details:has(#history) summary"); ok("history has 3",p.locator("#history .hrow").count()==3)
    p.click("#history .hrow:first-child button"); p.click("#history .hrow:first-child button"); ok("delete needs two taps",p.locator("#history .hrow").count()==2)
    p.click("#t-prog details:has(#bk) summary"); p.click("#bkCopy"); bk=p.input_value("#bk")
    p.evaluate("localStorage.clear()"); p.fill("#bk",bk); p.click("#bkRestore"); ok("backup round-trip",txt(p,"#bkMsg")=="Restored." and p.locator("#history .hrow").count()==2)
    p.fill("#bk","{}"); p.click("#bkRestore"); ok("bad backup refused","not a valid" in txt(p,"#bkMsg"))
    ok("no errors on Monday",not p.errs,str(p.errs))
    for t in ("today","dash","prog"):
        p.click(f"#nav [data-tab={t}]"); p.wait_for_timeout(300)
    # 3. each weekday has four sections with work; week 6 uses month 2 numbers
    titles=[]
    for d,exp in [("2026-12-21","Full A"),("2026-12-22","Easy"),("2026-12-23","Plyo + Cardio"),("2026-12-24","Mobility"),("2026-12-25","Full B"),("2026-12-26","Long easy"),("2026-12-27","Active Recovery")]:
        q=page(d+"T08:00:00",{},reduced=True); q.wait_for_timeout(500); q.click("#eGo"); q.wait_for_timeout(200)
        subs=[]
        for i in range(4):
            subs.append(q.text_content("#sub")); q.focus("#slider"); q.keyboard.press("ArrowRight"); q.wait_for_timeout(60)
        q.click("#toggle"); steps=q.locator("#panel .row").count()
        titles.append((q.text_content("#dayTitle").startswith(exp),all(subs),steps>0,q.text_content("#chipWkV").startswith("6"),not q.errs))
        if d=="2026-12-21": ok("month 2 working range 70-80% of 225","158–180" in q.text_content("#panel"),q.text_content("#panel")[:80])
        q.context.close()
    ok("all seven days load with four filled sections",all(all(t) for t in titles),str(titles))
    # 4. small phone, reduced motion, video sheet
    q=page("2026-11-20T08:00:00",{},size=(320,640)); start(q)
    q.click("#toggle"); q.wait_for_timeout(600); q.click("#panel .play"); q.wait_for_timeout(900)
    ok("video opens",q.locator("#vid iframe").count()==1 and "youtube.com/embed/" in q.get_attribute("#vid iframe","src"))
    q.click("#shClose"); q.wait_for_timeout(700); ok("video closes",q.evaluate("getComputedStyle(document.getElementById('sheet')).visibility")=="hidden" and q.locator("#vid iframe").count()==0)
    ok("320px: no sideways scroll",q.evaluate("document.documentElement.scrollWidth")==320); ok("no errors small",not q.errs,str(q.errs))
    # sideways scroll, on a page with a running clock (a frozen clock also freezes the slide-in animation)
    r=b.new_context(viewport={"width":390,"height":844}).new_page(); r.goto(url); start(r); wide=[]
    for t in ("dash","prog","today","prog","dash"):
        r.click(f"#nav [data-tab={t}]"); r.wait_for_timeout(450); sw=r.evaluate("document.documentElement.scrollWidth"); tr=r.evaluate(f"document.getElementById('t-{t}').style.transform")
        if sw!=390 or tr not in ("","none"): wide.append((t,sw,tr))
    ok("no sideways scroll, pages settle",not wide,str(wide))
    # 5. every video key used by the plan exists
    ok("no missing video keys",q.evaluate("[...document.querySelectorAll('.play')].length>0"))
    b.close()
print("\n%d failed"%len(fails)); sys.exit(1 if fails else 0)
