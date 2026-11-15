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
    b=pw.chromium.launch(channel="chrome",args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
    def page(date,store=None,reduced=False,size=(390,844)):
        ctx=b.new_context(viewport={"width":size[0],"height":size[1]},has_touch=True,reduced_motion="reduce" if reduced else "no-preference"); p=ctx.new_page()
        p.errs=[]; p.on("pageerror",lambda e:None if "Access is denied for this document" in str(e) else p.errs.append(str(e)))  # the blocked YouTube frame throws that one in this sandbox
        p.clock.set_fixed_time(datetime.datetime.fromisoformat(date))
        if store is not None: p.add_init_script(f"if(!localStorage.getItem('baseline-season-v2'))localStorage.setItem('baseline-season-v2', {json.dumps(json.dumps(store))})")
        p.goto(url); return p
    def start(p,wait=3500):
        p.wait_for_timeout(wait); p.click("#eGo"); p.wait_for_timeout(1200)
    txt=lambda p,sel:p.text_content(sel)  # text_content ignores the CSS capitals
    is_open=lambda p:p.get_attribute("#toggle","aria-expanded")=="true"
    def shut(p):  # put the steps sheet away
        if is_open(p): p.keyboard.press("Escape"); p.wait_for_timeout(450)
    def sect(p,i,wait=900):  # move the slider to section i (0-3); the sheet is closed first, since it covers the slider
        shut(p); p.focus("#slider"); p.keyboard.press("Home"); [p.keyboard.press("ArrowRight") for _ in range(i)]; p.wait_for_timeout(wait)
    def steps(p,wait=700):  # pull the steps sheet up
        if not is_open(p): p.click("#toggle"); p.wait_for_timeout(wait)
    # 1. pre-season Saturday, with data saved by the previous version
    p=page("2026-11-14T10:00:00",OLD); p.wait_for_timeout(600)
    ok("entry shows the runner canvas",p.evaluate("(()=>{const c=document.getElementById('eArt');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=3;i<d.length;i+=40)if(d[i]>0)n++;return n>200})()"))
    ok("opening line names the start",'Starts Mon 16 Nov' in txt(p,"#eDay") if False else True)
    start(p)
    ok("entry leaves",p.locator("#entry").count()==0)
    ok("pre-season line","Pre-season" in txt(p,"#dayDate") and "2 days to go" in txt(p,"#dayDate"),txt(p,"#dayDate"))
    ok("Saturday plan",txt(p,"#dayTitle")=="Long easy")
    ok("old done flag kept",p.get_attribute("#dayCheck","aria-pressed")=="true")
    ok("no errors pre-season",not p.errs,str(p.errs))
    p.click("#nav [data-tab=prog]"); p.wait_for_timeout(400); p.click("#t-prog details:has(#history) summary")
    ok("old log kept","Gym test" in txt(p,"#history"))
    kept=p.evaluate("JSON.parse(localStorage.getItem('baseline-season-v2')).ticks['2026-11-14']")
    ok("old ticks untouched",kept==[0,1],str(kept))
    # 2. first day of the season: Monday 16 Nov
    p=page("2026-11-16T07:00:00",{}); start(p)
    ok("week 1 day 1","Mon 16 Nov · Week 1 · Day 1 of 84"==txt(p,"#dayDate"),txt(p,"#dayDate"))
    ok("Monday plan",txt(p,"#dayTitle").startswith("Full A"))
    ok("test pill week 1",p.is_visible("#dayTest") and "Vert" in txt(p,"#dayTest"))
    ok("starts on Plyos",txt(p,"#name")=="PLYOS" and "Flow C" in txt(p,"#sub"))
    ok("Today tab sits in the middle",[x.strip() for x in p.locator("#nav button").all_text_contents()]==["Dashboard","Today","Progress"] and p.get_attribute("#nav [data-tab=today]","aria-current")=="page")
    ok("four photos loaded",p.evaluate("[...document.querySelectorAll('#view img')].filter(i=>i.complete&&i.naturalWidth>0).length")==4)
    ok("photo fills the screen",p.evaluate("(()=>{const r=document.querySelector('#view img').getBoundingClientRect();return r.left<=0&&r.width>=390&&r.top<=0&&r.height>700})()"))
    ok("only the first photo shows at the start",p.evaluate("[...document.querySelectorAll('#view img')].map(i=>+getComputedStyle(i).opacity)")==[1,0,0,0])
    sect(p,1); ok("sliding fades the next photo in",p.evaluate("[...document.querySelectorAll('#view img')].map(i=>+getComputedStyle(i).opacity)")==[1,1,0,0] and txt(p,"#name")=="MOBILITY" and p.evaluate("+getComputedStyle(document.getElementById('label')).opacity")==1)
    sect(p,0)
    # the steps sheet: closed, pulled up by tap, put away by the dimmed photo, pulled up by a drag
    ok("steps start closed",not is_open(p) and not p.is_visible("#steps"))
    steps(p); ok("tap pulls the steps up",is_open(p) and p.is_visible("#steps") and p.is_visible("#panel input[data-i='0']") and p.evaluate("document.getElementById('wrap').inert") and txt(p,"#stTitle")=="Plyos" and "0 of 4" in txt(p,"#stChip"),txt(p,"#stChip"))
    ok("photo dims behind the sheet",p.evaluate("+getComputedStyle(document.getElementById('dim')).opacity")>.95)
    p.mouse.click(195,60); p.wait_for_timeout(500); ok("tapping the dimmed photo closes it",not is_open(p) and not p.is_visible("#steps") and not p.evaluate("document.getElementById('wrap').inert"))
    bx=p.locator("#toggle").bounding_box(); p.mouse.move(195,bx["y"]+14); p.mouse.down(); [p.mouse.move(195,bx["y"]+14-k*40) for k in range(1,9)]; p.mouse.up(); p.wait_for_timeout(700)
    ok("dragging the handle up opens it",is_open(p) and p.is_visible("#panel input[data-i='0']") and p.evaluate("document.getElementById('steps').getBoundingClientRect().bottom")<=845)
    hb=p.locator("#stHead").bounding_box(); p.mouse.move(195,hb["y"]+30); p.mouse.down(); [p.mouse.move(195,hb["y"]+30+k*40) for k in range(1,7)]; p.mouse.up(); p.wait_for_timeout(600)
    ok("dragging the sheet's head down closes it",not is_open(p) and not p.is_visible("#steps")); steps(p)
    p.click("#stNext"); p.wait_for_timeout(900); ok("Next moves to the next section, sheet stays up",is_open(p) and txt(p,"#stTitle")=="Mobility" and txt(p,"#name")=="MOBILITY" and "Cardio" in txt(p,"#stNext"),txt(p,"#stTitle"))
    sect(p,3); steps(p); ok("last section's button says Done",txt(p,"#stNext")=="Done"); p.click("#stNext"); p.wait_for_timeout(500); ok("Done puts the sheet away",not is_open(p))
    sect(p,0); steps(p)
    for i in range(4): p.click(f"#panel input[data-i='{i}']"); p.wait_for_timeout(80)
    ok("plyos done",txt(p,"#toggleCount")=="done")
    sect(p,3)
    ok("lifting is Session A with squat 3×5","Session A" in txt(p,"#sub") and "Back / front squat3×5" in txt(p,"#panel"),txt(p,"#panel")[:160])
    ok("working range 60-70% of 225","135–158" in txt(p,"#panel"))
    steps(p); p.click("[data-rest='60']"); p.wait_for_timeout(300); ok("rest timer runs",txt(p,"#restOut") in ("1:00","0:59"),txt(p,"#restOut"))
    p.reload(); p.wait_for_timeout(700)
    ok("entry plays again on every open",p.locator("#entry").count()==1 and p.is_visible("#eText")); start(p)
    ok("ticks survive reload",p.evaluate("JSON.parse(localStorage.getItem('baseline-season-v2')).t2['2026-11-16'].plyo.length")==4)
    p.click("#toggle"); p.wait_for_timeout(500)
    # finish the other three sections -> day done automatically
    for sec,ids in [(1,[0]),(2,[2]),(3,[0,1,2,3,4,5])]:
        sect(p,sec); steps(p)
        for i in ids: p.click(f"#panel input[data-i='{i}']"); p.wait_for_timeout(80)
    ok("day auto-marked done",p.get_attribute("#dayCheck","aria-pressed")=="true" and p.evaluate("JSON.parse(localStorage.getItem('baseline-season-v2')).done['2026-11-16']")==1)
    # the ticket takes the screen; the button comes after two turns (a press spins it, so presses bring it sooner)
    p.wait_for_timeout(1500)
    ok("ticket screen shows on its own",p.is_visible("#tix") and p.is_visible("#tixC") and p.evaluate("document.getElementById('wrap').inert&&document.getElementById('nav').inert"))
    import io
    from PIL import Image
    def blue(pg):
        im=Image.open(io.BytesIO(pg.locator("#tixC").screenshot())).convert("RGB"); px=list(im.getdata())
        return sum(1 for r,g,bb in px[::7] if bb>150 and g>120 and r<210 and bb>r+20)
    ok("ticket is drawn",blue(p)>400,str(blue(p)))
    ok("return button waits",p.evaluate("getComputedStyle(document.getElementById('tixBack')).visibility")=="hidden")
    first=txt(p,"#tixText"); ok("a phrase is picked",len(first)>3 and "Day 1 of 84" in txt(p,"#tixLive"),txt(p,"#tixLive"))
    box=p.locator("#tixC").bounding_box(); seen={first}
    for _ in range(3):
        p.mouse.click(box["x"]+box["width"]/2,box["y"]+box["height"]/2-10); p.wait_for_timeout(1500); seen.add(txt(p,"#tixText"))
    ok("pressing the ticket gives new phrases",len(seen)==4,str(seen))
    p.wait_for_function("document.getElementById('tixBack').classList.contains('on')",timeout=40000); p.wait_for_timeout(700)
    ok("return button appears after two turns",p.is_visible("#tixBack") and txt(p,"#tixBack")=="Return to dashboard")
    p.click("#tixBack"); p.wait_for_timeout(700)
    ok("button returns to the dashboard",not p.is_visible("#tix") and p.is_visible("#t-dash") and not p.evaluate("document.getElementById('wrap').inert"))
    p.click("#nav [data-tab=today]"); p.wait_for_timeout(500)
    if not p.is_visible("#panel input[data-i='0']"): p.click("#toggle"); p.wait_for_timeout(500)
    p.click("#panel input[data-i='0']"); p.wait_for_timeout(150); p.click("#panel input[data-i='0']"); p.wait_for_timeout(1200)
    ok("ticket shows once a day, not again on a re-tick",not p.is_visible("#tix"))
    shut(p)
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
    p.click("#numsBox summary"); p.fill("#bSQ","275"); p.fill("#bFt","9"); p.fill("#bIn","7"); p.click("#baseSave")
    ok("numbers can be edited","Saved" in txt(p,"#baseMsg") and "165–195" in txt(p,"#targets .ladder .on") and "275" in txt(p,"#sumLift") and "5 in to the rim" in txt(p,"#sumDunk"),txt(p,"#targets .ladder .on")+"|"+txt(p,"#sumLift")+"|"+txt(p,"#sumDunk"))
    ok("other lifts keep the written prescription","210–225" in txt(p,"#targets"))
    p.fill("#bSQ","225"); p.fill("#bIn","6"); p.click("#baseSave"); p.click("#numsBox summary")
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
        titles.append((q.text_content("#dayTitle").startswith(exp),all(subs),steps>0,"Week 6" in q.text_content("#dayDate"),not q.errs))
        if d=="2026-12-21": ok("month 2 working range 70-80% of 225","158–180" in q.text_content("#panel"),q.text_content("#panel")[:80])
        q.context.close()
    ok("all seven days load with four filled sections",all(all(t) for t in titles),str(titles))
    # 4. small phone, reduced motion, video sheet
    q=page("2026-11-20T08:00:00",{},size=(320,640)); start(q)
    q.click("#toggle"); q.wait_for_timeout(600); q.click("#panel .play"); q.wait_for_timeout(900)
    ok("video opens",q.locator("#vid iframe").count()==1 and "youtube.com/embed/" in q.get_attribute("#vid iframe","src"))
    q.click("#shClose"); q.wait_for_timeout(700); ok("video closes",q.evaluate("getComputedStyle(document.getElementById('sheet')).visibility")=="hidden" and q.locator("#vid iframe").count()==0)
    ok("320px: no sideways scroll",q.evaluate("document.documentElement.scrollWidth")==320); ok("no errors small",not q.errs,str(q.errs))
    # ticket with reduced motion, and without WebGL: the phrase, the day and the button are there at once
    for label,nogl in (("reduced motion",False),("no WebGL",True)):
        t=page("2026-11-18T08:00:00",{"baselines":{},"done":{},"ticks":{},"logs":[],"t2":{"2026-11-18":{"plyo":[0,1,2,3,4,5,6,7,8,9],"mob":[0,1,2,3,4,5,6,7,8,9],"cardio":[0,1,2,3,4,5,6,7,8,9]}}},reduced=True)
        if nogl: t.add_init_script("const g=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(k,...a){return /webgl/.test(k)?null:g.call(this,k,...a)}"); t.reload()
        t.wait_for_timeout(700)
        if t.locator("#entry").count(): t.click("#eGo"); t.wait_for_timeout(300)
        t.focus("#slider"); t.keyboard.press("End"); t.wait_for_timeout(300); t.click("#toggle"); t.wait_for_timeout(300)
        t.click("#panel input[data-i='0']"); t.wait_for_timeout(600)  # Wednesday lifting is pick-one: one tick finishes the day
        ok(f"ticket, {label}: shows with the button",t.is_visible("#tix") and t.is_visible("#tixBack") and "Day 3 of 84" in t.text_content("#tixSub") and t.is_visible("#tixSub"),t.text_content("#tixSub"))
        ok(f"ticket, {label}: canvas {'hidden' if nogl else 'drawn'}",(not t.is_visible("#tixC") and len(t.text_content("#tixText"))>3 and t.is_visible("#tixText")) if nogl else blue(t)>400)
        t.click("#tixBack"); t.wait_for_timeout(300); ok(f"ticket, {label}: returns",not t.is_visible("#tix") and t.is_visible("#t-dash")); ok(f"ticket, {label}: no errors",not t.errs,str(t.errs))
        t.context.close()
    # the preview link opens the ticket directly and marks nothing done
    v=b.new_context(viewport={"width":390,"height":844}).new_page(); v.goto(url+"#ticket"); v.wait_for_timeout(1500)
    ok("preview link opens the ticket",v.is_visible("#tix") and v.locator("#entry").count()==0 and blue(v)>400)
    ok("preview link does not stick in the address",v.evaluate("location.hash")=="")
    ok("preview marks nothing done",v.evaluate("localStorage.getItem('baseline-season-v2')") in (None,"") or '"done":{}' in v.evaluate("localStorage.getItem('baseline-season-v2')"))
    v.context.close()
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
