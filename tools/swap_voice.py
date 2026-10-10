# -*- coding: utf-8 -*-
"""Point every audio reference at media/audio/marco and bump the build.
Run after scripts/revoice.py has produced all 726 clips."""
import json, os, re, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = "marco"; OLD = "george"
BUILD = sys.argv[1]
static = os.path.join(HERE, "app", "static.json")
d = json.load(open(static, encoding="utf-8"))
missing = []
for n in d["notes"]:
    if n.get("audio_path"):
        fn = os.path.basename(n["audio_path"])
    else:
        fn = "%03d_%s.mp3" % (n["id"], re.sub(r"[^a-z0-9]+", "_", (n["latin"] or "").lower()).strip("_")[:40])
    if not os.path.exists(os.path.join(HERE, "media", "audio", NEW, fn)):
        missing.append((n["id"], fn)); continue
    n["audio_path"] = "/media/audio/%s/%s" % (NEW, fn)
if missing:
    print("MISSING clips, aborting:", missing); sys.exit(1)
json.dump(d, open(static, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for rel in ("index.html", "app/index.html"):
    p = os.path.join(HERE, rel); s = open(p, encoding="utf-8").read()
    s = s.replace("/media/audio/%s/" % OLD, "/media/audio/%s/" % NEW)
    s = re.sub(r"var APP_BUILD = '[^']*'", "var APP_BUILD = '%s'" % BUILD, s)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
json.dump({"build": BUILD}, open(os.path.join(HERE, "app", "version.json"), "w", encoding="utf-8")); 
print("swapped; notes with audio:", sum(1 for n in d["notes"] if n.get("audio_path")))
