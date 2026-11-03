const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, PageOrientation, AlignmentType, BorderStyle } = require("docx");

const data = JSON.parse(fs.readFileSync(path.join(__dirname, "docdata.json"), "utf8"));
const FONT = "Arial";
const run = (text, o = {}) => new TextRun({ text, font: FONT, rightToLeft: true, size: 20, ...o });
const p = (text, o = {}, r = {}) => new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT,
  spacing: { after: 80 }, ...o, children: [run(text, r)] });
const h = (text, level) => new Paragraph({ heading: level, bidirectional: true, alignment: AlignmentType.RIGHT, children: [run(text, { bold: true, size: level === HeadingLevel.TITLE ? 36 : 28 })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, header, rows) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, w, head, fill) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    shading: head ? { type: ShadingType.CLEAR, fill: "2A2622", color: "auto" } : fill ? { type: ShadingType.CLEAR, fill, color: "auto" } : undefined,
    children: [p(text, { spacing: { after: 0 } }, head ? { bold: true, color: "FFFFFF" } : {})],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths, visuallyRightToLeft: true,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, widths[i], true)) }),
      ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((t, i) => cell(t, widths[i], false, i >= r.fillFrom ? "FFF8E1" : null)) }))],
  });
}
const withFill = (arr, from) => Object.assign(arr, { fillFrom: from });

// landscape A4 content width = 16838 - 2*1134
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 20 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", run: { font: FONT, size: 36, bold: true }, paragraph: { spacing: { before: 0, after: 120 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", run: { font: FONT, size: 28, bold: true }, paragraph: { spacing: { before: 320, after: 120 }, keepNext: true } },
    ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
      margin: { top: 1000, bottom: 1000, left: 1134, right: 1134 } } },
    children: [
      h("60 סיורים ל־60 שנה לאיחוד ירושלים – נתונים להשלמה", HeadingLevel.TITLE),
      p("המפה האינטראקטיבית מוכנה. כדי להשלים אותה נדרשים שני דברים, ועליהם ממלאים את העמודות המסומנות בצהוב:"),
      p("1. אישור או תיקון של תקצירי הסיפור לסיורים שאין להם תיק טיול (PDF) – התקצירים נכתבו לפי רשימת התחנות ולכן דורשים בדיקה של איש תוכן."),
      p("2. מיקום מדויק לסיורים שאין להם מפת Google – כרגע הנקודה במפה משוערת. עדיף קישור למפת Google My Maps של המסלול; אם אין, מספיקה כתובת נקודת ההתחלה."),

      h("חלק א׳ – תקצירי סיפור לבדיקה (" + data.blurbs.length + ")", HeadingLevel.HEADING_1),
      p("אם התקציר תקין – כתבו \"מאושר\" בעמודה האחרונה. אחרת – כתבו נוסח מתוקן (משפט–שניים).", {}, { italics: true, color: "595959" }),
      table([700, 3600, 5500, 4770], ["מס׳", "שם המסלול", "התקציר הנוכחי", "מאושר / נוסח מתוקן"],
        data.blurbs.map(b => withFill([String(b.n), b.name, b.text, ""], 3))),

      new Paragraph({ pageBreakBefore: true, bidirectional: true, children: [] }),
      h("חלק ב׳ – מיקומים משוערים במפה (" + data.pins.length + ")", HeadingLevel.HEADING_1),
      p("לסיור 38 (אלנבי) הטבלה המקורית הפנתה בטעות למפה של סיור אוסישקין – נדרש קישור למפה הנכונה.", {}, { italics: true, color: "595959" }),
      table([700, 3600, 3700, 3100, 3470], ["מס׳", "שם המסלול", "נקודת התחלה (מקטלוג מינהלת הטיולים)", "קישור למפת Google My Maps", "או: כתובת / קואורדינטות"],
        data.pins.map(x => withFill([String(x.n), x.name, x.start || x.guess, "", ""], 3))),
    ],
  }],
});
Packer.toBuffer(doc).then(b => {
  const out = path.join(__dirname, "..", "השלמת נתונים - 60 סיורים.docx");
  fs.writeFileSync(out, b); console.log(out);
});
