// create_cover_template.js
// Maakt cover_template.docx aan in de templates-map.
// Bevat {placeholders} op alle dynamische velden.
// Bewerk dit bestand in Word en sla op als cover_template.docx.

const {
  Document, Packer, Paragraph, Table, TableRow, TableCell,
  TextRun, WidthType, BorderStyle, AlignmentType,
  ShadingType, PageOrientation, convertInchesToTwip,
  TableBorders, VerticalAlign, HeightRule,
} = require("docx");
const fs   = require("fs");
const path = require("path");

const LIME  = "D4E84A";
const DARK  = "1A1A1A";
const TOPBG = "F2F5E8";
const SVBG  = "E8EDD5";
const SVGRN = "7A9A50";
const WHITE = "FFFFFF";
const FONT  = "Arial";

function t(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: opts.size ?? 20,
    bold: opts.bold ?? false, color: opts.color ?? DARK,
    italics: opts.italic ?? false });
}

function noBorder() {
  return { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
           left: { style: BorderStyle.NONE }, right:  { style: BorderStyle.NONE } };
}

function topCel(inhoud, bg, opts) {
  opts = opts || {};
  return new TableCell({
    children: inhoud,
    shading: { fill: bg, type: ShadingType.CLEAR, color: "auto" },
    verticalAlign: VerticalAlign.CENTER,
    margins: opts.margins || { top: 0, bottom: 0, left: 0, right: 0 },
    width: opts.width,
    borders: noBorder(),
  });
}

const splitBorder = {
  top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
  left: { style: BorderStyle.NONE },
  right: { style: BorderStyle.SINGLE, size: 2, color: "EEEEEE" },
};

const inhoud = [
  // 1. Lime accent-lijn
  new Paragraph({
    children: [t("", { size: 2 })],
    border: { top: { style: BorderStyle.SINGLE, size: 18, color: LIME, space: 0 } },
    spacing: { after: 0, before: 0 },
  }),

  // 2. Header
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: TableBorders.NONE,
    rows: [new TableRow({ children: [
      topCel([new Paragraph({
        children: [
          t("PandIQ", { size: 48, bold: true, color: DARK }),
          t("  WONEN", { size: 28, color: "999999" }),
        ],
        spacing: { after: 0 },
      })], TOPBG, { margins: { top: convertInchesToTwip(0.22), bottom: convertInchesToTwip(0.15), left: convertInchesToTwip(0.1), right: 80 } }),
      topCel([
        new Paragraph({ children: [t("Isolatie Quickscan", { size: 15, color: "AAAAAA" })], alignment: AlignmentType.RIGHT, spacing: { after: 40 } }),
        new Paragraph({ children: [t("Energierapport verduurzaming", { size: 15, color: "AAAAAA" })], alignment: AlignmentType.RIGHT, spacing: { after: 0 } }),
      ], TOPBG, { margins: { top: convertInchesToTwip(0.22), bottom: convertInchesToTwip(0.15), left: 80, right: convertInchesToTwip(0.1) } }),
    ]})],
  }),

  // 3. Street View placeholder
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top:     { style: BorderStyle.DASHED, size: 6, color: LIME },
      bottom:  { style: BorderStyle.DASHED, size: 6, color: LIME },
      left:    { style: BorderStyle.DASHED, size: 6, color: LIME },
      right:   { style: BorderStyle.DASHED, size: 6, color: LIME },
      insideH: { style: BorderStyle.NONE },
      insideV: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      height: { value: convertInchesToTwip(4.2), rule: HeightRule.EXACT },
      children: [new TableCell({
        children: [
          new Paragraph({ children: [t("\u25CE", { size: 48, color: "9EBF6A" })], alignment: AlignmentType.CENTER, spacing: { after: 80 } }),
          new Paragraph({ children: [t("Foto pand", { bold: true, size: 22, color: SVGRN })], alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
          new Paragraph({ children: [t("Google Street View", { size: 18, color: "AAAAAA" })], alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
          new Paragraph({ children: [t("{adres}", { size: 16, color: "BBBBBB" })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
        ],
        shading: { fill: SVBG, type: ShadingType.CLEAR, color: "auto" },
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 0, bottom: 0, left: 0, right: 0 },
        borders: noBorder(),
      })],
    })],
  }),

  // 4. Lime separator
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: TableBorders.NONE,
    rows: [new TableRow({
      height: { value: convertInchesToTwip(0.07), rule: HeightRule.EXACT },
      children: [topCel([new Paragraph({ children: [t("")], spacing: { after: 0 } })], LIME)],
    })],
  }),

  // 5. Adres en datum
  new Paragraph({ children: [t("")], spacing: { after: 80 } }),
  new Paragraph({
    children: [t("{straat}", { bold: true, size: 36, color: DARK })],
    spacing: { after: 80 },
  }),
  new Paragraph({
    children: [
      t("{postcode_plaats}", { size: 22, color: "888888" }),
      t("  \u00B7  ", { size: 22, color: "CCCCCC" }),
      t("{datum}", { size: 22, color: "888888" }),
    ],
    spacing: { after: 0 },
  }),

  // Scheidingslijn
  new Paragraph({
    children: [t("", { size: 2 })],
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "EEEEEE", space: 4 } },
    spacing: { before: 120, after: 140 },
  }),

  // 6. Data-cards
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: TableBorders.NONE,
    rows: [new TableRow({ children: [

      // Energielabel
      new TableCell({
        children: [
          new Paragraph({ children: [t("Energielabel", { size: 16, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
          new Paragraph({ children: [t("{energielabel}", { bold: true, size: 28, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
        ],
        shading: { fill: "F7FAF0", type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 120, bottom: 120, left: 80, right: 80 },
        borders: splitBorder,
      }),

      // Bouwjaar
      new TableCell({
        children: [
          new Paragraph({ children: [t("Bouwjaar", { size: 16, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
          new Paragraph({ children: [t("{bouwjaar}", { bold: true, size: 32, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
        ],
        shading: { fill: "F7FAF0", type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 120, bottom: 120, left: 80, right: 80 },
        borders: splitBorder,
      }),

      // Warmtebehoefte
      new TableCell({
        children: [
          new Paragraph({ children: [t("Warmtebehoefte", { size: 16, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
          new Paragraph({ children: [t("{warmtebehoefte} kWh", { bold: true, size: 28, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 20 } }),
          new Paragraph({ children: [t("per m\u00B2/jaar", { size: 15, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
        ],
        shading: { fill: "F7FAF0", type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 120, bottom: 120, left: 80, right: 80 },
        borders: splitBorder,
      }),

      // ISDE-subsidie (lime)
      new TableCell({
        children: [
          new Paragraph({ children: [t("ISDE-subsidie", { size: 16, color: "3A3A3A" })], alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
          new Paragraph({ children: [t("tot {subsidie_totaal}", { bold: true, size: 28, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 20 } }),
          new Paragraph({ children: [t("indicatief", { size: 15, color: "555555" })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
        ],
        shading: { fill: LIME, type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 120, bottom: 120, left: 80, right: 80 },
        borders: noBorder(),
      }),

    ]})],
  }),

  // Scheidingslijn
  new Paragraph({
    children: [t("", { size: 2 })],
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: "EEEEEE", space: 4 } },
    spacing: { before: 100, after: 100 },
  }),

  // 7. Footer
  new Paragraph({
    children: [t("{woningtype}  \u00B7  {oppervlakte} m\u00B2  \u00B7  {bouwperiode}", { size: 18, color: "AAAAAA" })],
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [t("Indicatief rapport op basis van openbare registraties (BAG & EP-Online)", { size: 16, color: "CCCCCC" })],
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [t("Aan dit rapport kunnen geen rechten worden ontleend", { size: 16, color: "CCCCCC" })],
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [t("pandiq.nl", { bold: true, size: 20, color: LIME })],
    alignment: AlignmentType.RIGHT,
    spacing: { after: 0 },
  }),
];

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { orientation: PageOrientation.PORTRAIT, width: convertInchesToTwip(8.27), height: convertInchesToTwip(11.69) },
        margin: { top: convertInchesToTwip(0.6), bottom: convertInchesToTwip(0.6), left: convertInchesToTwip(0.6), right: convertInchesToTwip(0.6) },
      },
    },
    children: inhoud,
  }],
});

const uitvoer = path.join(__dirname, "..", "templates", "cover_template.docx");

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(uitvoer, buf);
  const kb = (fs.statSync(uitvoer).size / 1024).toFixed(1);
  console.log(`Template aangemaakt: ${uitvoer} (${kb} kB)`);
  console.log("");
  console.log("Placeholders in dit bestand:");
  console.log("  {adres}           - volledig adres (in Street View label)");
  console.log("  {straat}          - straat + huisnummer (grote kop)");
  console.log("  {postcode_plaats} - postcode en plaats");
  console.log("  {datum}           - rapportdatum");
  console.log("  {energielabel}    - labelklasse (A t/m G)");
  console.log("  {bouwjaar}        - bouwjaar woning");
  console.log("  {warmtebehoefte}  - warmtebehoefte in kWh/m²/jaar");
  console.log("  {subsidie_totaal} - totaal ISDE-subsidie in euros");
  console.log("  {woningtype}      - woningtype");
  console.log("  {oppervlakte}     - gebruiksoppervlakte in m²");
  console.log("  {bouwperiode}     - bouwperiode omschrijving");
  console.log("");
  console.log("Open het bestand in Word, pas het ontwerp aan en sla op als cover_template.docx.");
});
