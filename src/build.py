import json, math, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
from stories import STORIES, APPROX
PATHS = json.load(open(os.path.join(here, "paths.json"), encoding="utf-8")) if os.path.exists(os.path.join(here, "paths.json")) else {}

def km(a, b):  # haversine, [lat, lng]
    p = math.pi / 180
    h = math.sin((b[0]-a[0])*p/2)**2 + math.cos(a[0]*p)*math.cos(b[0]*p)*math.sin((b[1]-a[1])*p/2)**2
    return 12742 * math.asin(math.sqrt(h))

TOPICS = ["נוסעים, חוקרים ומבקרים בירושלים", "מנהיגים וחלוצים בירושלים", "שכונות ועדות בירושלים",
          "רבנים בירושלים", "בוני ירושלים", "יובל שנים לאיחוד ירושלים", "מחנכים, משוררים וסופרים בירושלים"]
out = []
for r in json.load(open(os.path.join(here, "data.json"), encoding="utf-8")):
    n, name = r["n"], r["name"]
    topic = next((t for t in TOPICS if name.startswith(t)), "מסלולי עיר ונוף")
    title = name[len(topic):].lstrip(" -") if topic in name else name
    stops = [{"name": s["name"], "lat": s["lat"], "lng": s["lng"]} for s in r.get("stops", [])
             if 31.6 < s["lat"] < 31.9 and 35.1 < s["lng"] < 35.3]  # drop placeholder/out-of-town points
    if stops: lat, lng, approx = stops[0]["lat"], stops[0]["lng"], False
    else: lat, lng, _ = APPROX[n]; approx = True
    pdf = ("https://meyda.education.gov.il/files/" + r["pdf"]) if r["pdf"] else r.get("pdf_from_page", "")
    m = re.search(r'אורך המסלול:\s*כ\s*-\s*([\d.]+)\s*ק"מ', r.get("desc", ""))
    out.append({
        "n": n, "name": name, "topic": topic, "title": title, "story": STORIES[n],
        "desc": re.sub(r'^אורך המסלול:[^\n]*\n', "", r.get("desc", "")), "start": r.get("start", ""),
        "length": f'{m.group(1)} ק"מ' if m else "", "difficulty": r.get("difficulty", ""), "accessible": r.get("accessible", ""),
        "catalog": f"https://tiulim.education.gov.il/trips-katalog/{r['slug']}/" if r["slug"] else "https://tiulim.education.gov.il/trips-katalog/?searchers=8012",
        "pdf": pdf, "gmap": f"https://www.google.com/maps/d/viewer?mid={r['mid']}" if r.get("mid") else "",
        "lat": lat, "lng": lng, "approx": approx, "stops": stops,
        # walking path per leg; legs where the router detoured (>3x straight distance) fall back to a dashed straight connector
        "legs": [{"pts": [[stops[i]["lat"], stops[i]["lng"]], [stops[i+1]["lat"], stops[i+1]["lng"]]], "dashed": True}
                 if (i + 1) in PATHS[str(n)]["detours"] else {"pts": leg}
                 for i, leg in enumerate(PATHS[str(n)]["legs"])] if str(n) in PATHS else [],
    })
for t in out:  # walking length along the drawn line (detour legs count as straight)
    t["walk_km"] = round(sum(km(a, b) for l in t["legs"] for a, b in zip(l["pts"], l["pts"][1:])), 1) if t["legs"] else None
assert len(out) == 61 and all(t["story"] for t in out)
json.dump(out, open(os.path.join(here, "trails.json"), "w", encoding="utf-8"), ensure_ascii=False)  # reused by make_xlsx.py
dest = os.path.dirname(here)  # repo root
html = open(os.path.join(here, "template.html"), encoding="utf-8").read().replace("/*DATA*/", json.dumps(out, ensure_ascii=False))
open(os.path.join(dest, "index.html"), "w", encoding="utf-8").write(html)
print("ok", sum(t["approx"] for t in out), "approx;", sum(len(t["stops"]) > 1 for t in out), "with routes")
