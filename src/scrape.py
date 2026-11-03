import re, html, json, subprocess, os, sys, urllib.request, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from rows import ROWS

OUT = os.path.join(os.path.dirname(__file__), "dl")
UA = {"User-Agent": "Mozilla/5.0"}

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read()
    except Exception as e:
        return None

def field(t, label):
    m = re.search(label + r":?\s*\n\s*([^\n]+)", t)
    return m.group(1).strip() if m else ""

def catalog(slug):
    raw = get(f"https://tiulim.education.gov.il/trips-katalog/{slug}/")
    if not raw: return {}
    s = raw.decode("utf-8", "ignore")
    pdf = re.findall(r'href="(https?://meyda[^"]+\.pdf)"', s)
    s = re.sub(r"(?s)<(script|style)[^>]*>.*?</\1>", "", s)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", s))
    t = re.sub(r"[ \t\r]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
    desc = re.search(r"תיאור המסלול\s*\n(.*?)\n\s*(?:מפת המסלול|המסלול המלא|הוראות הגעה)", t, re.S)
    return {
        "desc": desc.group(1).strip() if desc else "",
        "start": field(t, "הוראות הגעה"),
        "difficulty": field(t, "דרגת קושי"),
        "theme": field(t, "מסלול נושאי"),
        "subarea": field(t, "תת אזור"),
        "accessible": field(t, "נגישות לכיסא גלגלים"),
        "pdf_from_page": pdf[0] if pdf else "",
    }

def kml(mid):
    for m in dict.fromkeys([mid, mid.replace("-", "")]):  # hyphens may be PDF line-wrap artifacts
        raw = get(f"https://www.google.com/maps/d/kml?mid={m}&forcekml=1")
        if not raw or b"<kml" not in raw: continue
        ns = {"k": "http://www.opengis.net/kml/2.2"}
        root = ET.fromstring(raw)
        stops = []
        for p in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
            c = p.find(".//k:Point/k:coordinates", ns)
            if c is None: continue
            lng, lat = map(float, c.text.strip().split(",")[:2])
            d = p.findtext("k:description", "", ns)
            d = html.unescape(re.sub(r"<[^>]+>", " ", d)).strip()
            stops.append({"name": (p.findtext("k:name", "", ns) or "").strip(), "lat": lat, "lng": lng, "desc": d[:600]})
        return {"mid": m, "map_title": root.findtext(".//k:Document/k:name", "", ns), "stops": stops}
    return {"mid_failed": mid}

def pdf_intro(path, n):
    if not path: return ""
    raw = get("https://meyda.education.gov.il/files/" + path)
    if not raw or not raw.startswith(b"%PDF"): return "FETCH_FAILED"
    f = os.path.join(OUT, f"{n}.pdf"); open(f, "wb").write(raw)
    txt = subprocess.run(["pdftotext", "-l", "4", "-enc", "UTF-8", f, "-"], capture_output=True).stdout.decode("utf-8", "ignore")
    txt = re.sub("[‎‏‪-‮]", "", txt)
    return re.sub(r"\s+", " ", txt).strip()[:3000]

def one(row):
    n, name, slug, pdf, mid = row
    r = {"n": int(n), "name": name, "slug": slug, "pdf": pdf}
    if slug: r.update(catalog(slug))
    if mid: r.update(kml(mid))
    r["pdf_text"] = pdf_intro(pdf or (r.get("pdf_from_page") or "").split("/files/")[-1] if (pdf or r.get("pdf_from_page")) else "", n)
    return r

os.makedirs(OUT, exist_ok=True)
with ThreadPoolExecutor(8) as ex:
    res = list(ex.map(one, ROWS))
json.dump(res, open(os.path.join(os.path.dirname(__file__), "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in res:
    print(r["n"], "desc" if r.get("desc") else "-", len(r.get("stops", [])), "stops" , "MIDFAIL" if r.get("mid_failed") else "", "pdf:", len(r.get("pdf_text", "")))
