# Fetch walking paths between each trail's stops (OSM foot routing, routing.openstreetmap.de) -> paths.json
# ponytail: computed once at build time, so the page stays a single file and never calls the router.
import json, math, os, time, urllib.request
here = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(here, "data.json"), encoding="utf-8"))
OUT = os.path.join(here, "paths.json")
paths = {}

def km(a, b):  # haversine, (lat, lng)
    p = math.pi / 180
    h = math.sin((b[0]-a[0])*p/2)**2 + math.cos(a[0]*p)*math.cos(b[0]*p)*math.sin((b[1]-a[1])*p/2)**2
    return 12742 * math.asin(math.sqrt(h))

for r in data:
    stops = [s for s in r.get("stops", []) if 31.6 < s["lat"] < 31.9 and 35.1 < s["lng"] < 35.3]  # same filter as build.py
    if len(stops) < 2 or str(r["n"]) in paths: continue
    coords = ";".join(f'{s["lng"]},{s["lat"]}' for s in stops)
    url = f"https://routing.openstreetmap.de/routed-foot/route/v1/foot/{coords}?overview=full&geometries=geojson"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jerusalem-60-trails/1.0"}), timeout=60) as resp:
            j = json.load(resp)
        route = j["routes"][0]
        line = []
        for lng, lat in route["geometry"]["coordinates"]:
            pt = [round(lat, 5), round(lng, 5)]
            if not line or line[-1] != pt: line.append(pt)
        straight = [km((a["lat"], a["lng"]), (b["lat"], b["lng"])) for a, b in zip(stops, stops[1:])]
        walked = [l["distance"] / 1000 for l in route["legs"]]
        detours = [i + 1 for i, (s, w) in enumerate(zip(straight, walked)) if w > 0.3 and w > 3 * s]  # leg walks >3x the straight distance
        # split the overview line into legs at the snapped waypoints (nearest point, searching forward)
        cuts, k = [0], 0
        for wp in j["waypoints"][1:-1]:
            lng, lat = wp["location"]
            k = min(range(k, len(line)), key=lambda i: (line[i][0]-lat)**2 + (line[i][1]-lng)**2)
            cuts.append(k)
        cuts.append(len(line) - 1)
        legs = [line[a:b + 1] for a, b in zip(cuts, cuts[1:])]
        paths[str(r["n"])] = {"legs": legs, "km": round(route["distance"] / 1000, 1), "detours": detours}
        print(r["n"], paths[str(r["n"])]["km"], "km", len(line), "pts", "DETOUR legs:" if detours else "", detours or "")
    except Exception as e:
        print(r["n"], "FAILED", e)
    json.dump(paths, open(OUT, "w", encoding="utf-8"))
    time.sleep(1)  # be polite to the free server
