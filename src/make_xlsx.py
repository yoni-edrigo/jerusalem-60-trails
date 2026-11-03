# Summary spreadsheet of all 61 trails -> ~/Documents/GitHub/jerusalem-60-trails/60-trails.xlsx
import json, math, os, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

here = os.path.dirname(os.path.abspath(__file__))
trails = json.load(open(os.path.join(here, "trails.json"), encoding="utf-8"))
REVIEW = {5, 6, 8, 11, 13, 14, 23, 30, 32, 33, 34, 35, 37, 38, 39, 42, 47, 48, 49, 51, 53, 59, 61}  # blurbs written without a trip PDF

def km(a, b):
    p = math.pi / 180
    h = math.sin((b[0]-a[0])*p/2)**2 + math.cos(a[0]*p)*math.cos(b[0]*p)*math.sin((b[1]-a[1])*p/2)**2
    return 12742 * math.asin(math.sqrt(h))
def line_km(pts): return sum(km(a, b) for a, b in zip(pts, pts[1:]))

F = "Arial"
HEAD = Font(name=F, bold=True, color="FFFFFF"); BODY = Font(name=F); LINK = Font(name=F, color="0563C1", underline="single")
HFILL = PatternFill("solid", fgColor="2A2622"); REVFILL = PatternFill("solid", fgColor="FFF2CC")
WRAP = Alignment(wrap_text=True, vertical="top", horizontal="right", readingOrder=2)
TOP = Alignment(vertical="top", horizontal="right", readingOrder=2)
thin = Side(style="thin", color="D9D9D9"); BORDER = Border(top=thin, bottom=thin, left=thin, right=thin)

COLS = [  # header, width, wrap
    ("מס׳", 6, False), ("נושא", 22, True), ("שם המסלול", 30, True), ("שם מלא (מהטבלה המקורית)", 40, True),
    ('אורך לפי הקטלוג (ק"מ)', 12, False), ('אורך מחושב – מסלול הליכה (ק"מ)', 14, False),
    ('אורך (ק"מ)', 10, False), ("מקור האורך", 10, False),
    ("דרגת קושי", 10, False), ("נגיש לכיסא גלגלים", 10, False), ("נקודת התחלה", 40, True),
    ("קו רוחב", 11, False), ("קו אורך", 11, False), ("מיקום משוער", 9, False),
    ("מס׳ תחנות", 8, False), ("תחנות (JSON)", 60, True), ("תקציר הסיפור", 60, True), ("תקציר לבדיקה", 9, False),
    ("תיאור המסלול (מקטלוג מינהלת הטיולים)", 70, True), ("מקטעים עם עקיפה (קו מקווקו)", 12, False),
    ("דף במינהלת הטיולים", 22, False), ("תיק טיול (PDF)", 22, False), ("מפת Google", 22, False),
]

wb = Workbook()
ws = wb.active; ws.title = "סיורים"; ws.sheet_view.rightToLeft = True
for i, (h, w, _) in enumerate(COLS, 1):
    c = ws.cell(1, i, h); c.font = HEAD; c.fill = HFILL; c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center", readingOrder=2); c.border = BORDER
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[1].height = 45

for r, t in enumerate(sorted(trails, key=lambda t: t["n"]), 2):
    m = re.match(r"([\d.]+)", t["length"] or "")
    catalog_km = float(m.group(1)) if m else None
    walk_km = t["walk_km"]  # computed in build.py along the same line the map draws
    stops = json.dumps([{"n": i + 1, "name": s["name"], "lat": s["lat"], "lng": s["lng"]} for i, s in enumerate(t["stops"])], ensure_ascii=False)
    detours = ", ".join(str(i + 1) for i, l in enumerate(t["legs"]) if l.get("dashed"))
    row = [t["n"], t["topic"], t["title"], t["name"], catalog_km, walk_km,
           f'=IF(ISNUMBER(E{r}),E{r},IF(ISNUMBER(F{r}),F{r},""))',
           f'=IF(ISNUMBER(E{r}),"קטלוג",IF(ISNUMBER(F{r}),"מחושב","חסר"))',
           t["difficulty"] or None, t["accessible"] or None, t["start"] or None,
           t["lat"], t["lng"], "כן" if t["approx"] else "לא",
           len(t["stops"]), stops if t["stops"] else None, t["story"], "כן" if t["n"] in REVIEW else "לא",
           t["desc"] or None, detours or None, t["catalog"], t["pdf"] or None, t["gmap"] or None]
    for i, v in enumerate(row, 1):
        c = ws.cell(r, i, v); c.font = BODY; c.border = BORDER
        c.alignment = WRAP if COLS[i - 1][2] else TOP
        if i in (21, 22, 23) and v:
            c.hyperlink = v; c.font = LINK
    ws.cell(r, 5).number_format = ws.cell(r, 6).number_format = ws.cell(r, 7).number_format = "0.0"
    ws.cell(r, 12).number_format = ws.cell(r, 13).number_format = "0.00000"
    if t["n"] in REVIEW: ws.cell(r, 17).fill = ws.cell(r, 18).fill = REVFILL
    if t["approx"]: ws.cell(r, 12).fill = ws.cell(r, 13).fill = ws.cell(r, 14).fill = REVFILL
    ws.row_dimensions[r].height = 90
last = len(trails) + 1
ws.freeze_panes = "D2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(COLS))}{last}"

# legend / sources sheet
lg = wb.create_sheet("מקרא ומקורות"); lg.sheet_view.rightToLeft = True
lg.column_dimensions["A"].width = 34; lg.column_dimensions["B"].width = 100
rows = [
    ("סיכום", None),
    ("מספר סיורים", f"=COUNTA('סיורים'!A2:A{last})"),
    ('סה"כ אורך (ק"מ)', f"=SUM('סיורים'!G2:G{last})"),
    ("סיורים עם מסלול הליכה מחושב", f"=COUNT('סיורים'!F2:F{last})"),
    ("סיורים עם מיקום משוער", f"=COUNTIF('סיורים'!N2:N{last},\"כן\")"),
    ("תקצירים לבדיקה", f"=COUNTIF('סיורים'!R2:R{last},\"כן\")"),
    (None, None),
    ("עמודות", None),
    ('אורך לפי הקטלוג', 'מתוך "אורך המסלול" בדף הסיור באתר מינהלת הטיולים (tiulim.education.gov.il).'),
    ('אורך מחושב', 'אורך מסלול ההליכה בין התחנות, לפי ניתוב הליכה של OpenStreetMap (routing.openstreetmap.de). מקטעים שבהם הניתוב עקף (מעל פי 3 מהמרחק הישיר) נמדדו בקו ישר.'),
    ('אורך', 'נוסחה: אורך הקטלוג אם קיים, אחרת האורך המחושב.'),
    ('תחנות (JSON)', 'מערך JSON של התחנות מתוך מפת Google My Maps של הסיור: n = מספר תחנה, name = שם, lat/lng = קואורדינטות.'),
    ('מיקום משוער', 'לסיור אין מפת Google עם תחנות; הנקודה במפה הוצבה ידנית בנקודת ההתחלה.'),
    ('תקציר הסיפור', 'נכתב על בסיס תיק הטיול (PDF). "תקציר לבדיקה = כן" – אין לסיור תיק טיול, והתקציר נכתב לפי התחנות ודורש אישור של איש תוכן.'),
    ('מקטעים עם עקיפה', 'מספרי המקטעים (מתחנה k לתחנה k+1) שמוצגים במפה כקו מקווקו במקום מסלול הליכה.'),
    (None, None),
    ("סימון צבע", None),
    ("רקע צהוב", "נתון שדורש בדיקה או השלמה: תקציר לבדיקה, או מיקום משוער."),
    (None, None),
    ("הערות", None),
    ("סיור 38 (אלנבי)", "בטבלה המקורית קישור המפה היה של סיור אוסישקין (47); הקישור הועבר לסיור 47 ולסיור 38 חסרה מפה."),
    ("סיורים 1–2", "אין דף ייעודי באתר מינהלת הטיולים – הקישור הוא לחיפוש בקטלוג."),
]
for i, (a, b) in enumerate(rows, 1):
    ca, cb = lg.cell(i, 1, a), lg.cell(i, 2, b)
    for c in (ca, cb): c.font = BODY; c.alignment = Alignment(wrap_text=True, vertical="top", horizontal="right", readingOrder=2)
    if a and b is None: ca.font = Font(name=F, bold=True, size=12)
lg.cell(3, 2).number_format = "0.0"

out = os.path.join(os.path.dirname(here), "60 סיורים - נתונים.xlsx")
wb.save(out)
