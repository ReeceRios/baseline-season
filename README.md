# Baseline Season — phone app

Reece's 12-week tracker (16 Nov 2026 – 7 Feb 2027): dunk, Hang Clean / Squat / Deadlift, 5K and 10K.
An installable web app: no server, no app store. Data stays on the phone.

## Put it on your phone

1. Host this folder on any static host with HTTPS. Easiest: drag the folder onto https://app.netlify.com/drop. GitHub Pages and Cloudflare Pages also work.
2. Open the link on your phone.
   - iPhone: Safari → Share → Add to Home Screen.
   - Android: Chrome → menu → Install app (or Add to Home screen).
3. Open it from the home screen. It runs full screen and works offline after the first load.

Anyone with the link can open the page (it shows your name, height and baselines). Your logs are never uploaded.

## What it does

- Today card and week strip roll forward from the 16 Nov start date. Check-offs are saved per date.
- Opening screen on each launch with today's session; the header strip shows all 84 days of the season.
- Today's steps: tap each one as you finish it. Ticking them all marks the day done.
- Rest timer: 60, 90 or 120 seconds, with a beep and (on Android) a buzz. Keep the app open: it can't alert from a locked phone.
- Season calendar (Week tab): all 12 weeks, done days filled, tap a day for its details.
- Log a workout, a lift, a vert test (jump reach) or a 5K / 10K time.
- A lift logged as "New tested max" moves your current max and the % load table. Starting baselines stay fixed so you see the gain.
- Backup card: copy your data as text, paste it back to restore (also how you move to a new phone).

## Files

- `index.html` — the whole app
- `manifest.webmanifest`, `icons/` — home-screen name and icon
- `fonts/dm-sans.woff2` — DM Sans, SIL Open Font License (`fonts/OFL.txt`)
- `sw.js` — offline cache. An update shows the next time the app is opened.
- `version.json` — the build number. For each release, raise it together with `BUILD` in `index.html` and the cache name in `sw.js`; an app left open reloads itself when it sees a newer number.
- `test.py` — self-check (`pip install playwright && python test.py`)

To change the start date, edit `START` near the top of the script in `index.html`.
