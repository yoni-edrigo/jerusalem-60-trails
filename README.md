# 60 סיורים ל־60 שנה לאיחוד ירושלים

Interactive map of 61 Jerusalem trails, made for the Ministry of Education's trips department (מינהלת הטיולים). Each trail on the map has its story, stops, walking route, and links to its trip file (PDF) and catalog page.

| File | What |
|---|---|
| `index.html` | The page: one self-contained, responsive file (RTL, iOS-style on mobile, installable as a home-screen app) |
| `60 סיורים - נתונים.xlsx` | All trail data: lengths, stops as JSON, links |
| `השלמת נתונים - 60 סיורים.docx` | Form for the client: blurbs to review and missing map locations |

## Rebuilding (`src/`)

```
python -I src/scrape.py      # catalog pages + Google My Maps stops + PDF intros -> src/data.json   (slow, network)
python -I src/paths.py       # walking routes between stops (routing.openstreetmap.de) -> src/paths.json   (~1 req/s)
python -I src/build.py       # -> index.html
python -I src/make_xlsx.py   # -> the spreadsheet (needs openpyxl; open and save once in Excel to cache formula values)
node src/makedoc.js          # -> the Word form (needs: npm i docx)
```

- Trail list, catalog slugs, PDF paths and map IDs: `src/rows.py` (transcribed from the meeting table).
- Story blurbs and approximate start points: `src/stories.py`.
- Page markup, styles and code: `src/template.html`. `build.py` injects the data.

Map tiles come from Esri. OpenStreetMap's own tile server blocks pages opened from `file://`.
