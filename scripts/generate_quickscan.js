// generate_quickscan.js
// Genereert een PandIQ Isolatie Quickscan .docx op basis van woningdata.
// Gebruik: node generate_quickscan.js

const {
  Document, Packer, Paragraph, Table, TableRow, TableCell,
  TextRun, WidthType, BorderStyle, AlignmentType,
  ShadingType, PageOrientation, convertInchesToTwip,
  TableBorders, VerticalAlign, PageBreak, HeightRule,
} = require("docx");
const fs            = require("fs");
const path          = require("path");
const PizZip        = require("pizzip");
const Docxtemplater = require("docxtemplater");

// ── Woningdata ────────────────────────────────────────────────────────────────

const data = {
  adres:             "Helper Weststraat 42, 9721BS Groningen",
  datum:             "4 mei 2026",
  bouwjaar:          1933,
  bouwperiode:       "voor 1975",
  oppervlakte:       66,
  woningtype:        "Appartement",
  energielabel:      "D",
  energiebehoefte:   176.9,
  warmtebehoefte:    177.3,
  maatregelen: [
    {
      naam: "Gevelisolatie", onderdeel: "Gevel", urgentie: "Hoog", score: 4,
      oppervlakte: 18, besparing_min: 284, besparing_max: 384,
      investering_min: 3238, investering_max: 4255, subsidie: 375,
      terugverdientijd: "8-14 jaar",
    },
    {
      naam: "HR++ dubbelglas", onderdeel: "Glas", urgentie: "Hoog", score: 4,
      oppervlakte: 4, besparing_min: 162, besparing_max: 219,
      investering_min: 320, investering_max: 600, subsidie: 50,
      terugverdientijd: "1-3 jaar",
    },
    {
      naam: "Vloerisolatie", onderdeel: "Vloer", urgentie: "Hoog", score: 4,
      oppervlakte: 28, besparing_min: 122, besparing_max: 165,
      investering_min: 609, investering_max: 831, subsidie: 152,
      terugverdientijd: "3-6 jaar",
    },
  ],
  totaal_investering_min: 4167,
  totaal_investering_max: 5686,
  totaal_subsidie:        577,
  totaal_besparing_min:   568,
  totaal_besparing_max:   768,
  terugverdientijd_min:   5,
  terugverdientijd_max:   9,
};

// ── Kleur- en stijlconstanten ─────────────────────────────────────────────────

const LIME  = "D4E84A";  // hoofdkleur (pill, tabelkop, PandIQ-blok)
const DARK  = "1A1A1A";  // koppen en vetgedrukte tekst
const MID   = "444444";  // lopende tekst
const LIGHT = "F9FBE7";  // afwisselende tabelrijen
const WHITE = "FFFFFF";
const FONT  = "Arial";

// ── Basiscomponenten ──────────────────────────────────────────────────────────

function t(text, opts = {}) {
  return new TextRun({
    text,
    font:    FONT,
    size:    opts.size    ?? 20,
    bold:    opts.bold    ?? false,
    color:   opts.color   ?? DARK,
    italics: opts.italic  ?? false,
  });
}

function p(children, opts = {}) {
  const runs = Array.isArray(children) ? children : [t(children, opts)];
  return new Paragraph({
    children: runs,
    alignment: opts.align ?? AlignmentType.LEFT,
    spacing: {
      before: opts.before ?? 0,
      after:  opts.after  ?? 140,
      line:   opts.line   ?? 276,
    },
  });
}

function lege() {
  return new Paragraph({ children: [t("")], spacing: { after: 0 } });
}

function eur(val) {
  return "€\u202F" + Math.round(val).toLocaleString("nl-NL");
}

// ── Tabel-hulpfuncties ────────────────────────────────────────────────────────

function cel(tekst, opts = {}) {
  return new TableCell({
    children: [new Paragraph({
      children: [t(tekst, {
        bold:   opts.bold   ?? false,
        size:   opts.size   ?? 18,
        color:  opts.color  ?? (opts.bg === LIME ? DARK : DARK),
        italic: opts.italic ?? false,
      })],
      alignment: opts.align ?? AlignmentType.LEFT,
      spacing: { after: 0, line: 276 },
    })],
    shading: opts.bg ? { fill: opts.bg, type: ShadingType.CLEAR, color: "auto" } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    columnSpan: opts.span ?? 1,
    borders: opts.borders ?? undefined,
  });
}

// Tabel zonder buitenrand, subtiele binnenrand
function dunneRanden() {
  const lijn = { style: BorderStyle.SINGLE, size: 2, color: "DDDDDD" };
  const geen = { style: BorderStyle.NONE,   size: 0, color: "FFFFFF" };
  return { top: geen, bottom: geen, left: geen, right: geen, insideH: lijn, insideV: geen };
}

// Tabel met lichte volledige rand
function volleRanden() {
  const lijn = { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" };
  return { top: lijn, bottom: lijn, left: lijn, right: lijn, insideH: lijn, insideV: lijn };
}

// ── Sectiekoppen ──────────────────────────────────────────────────────────────

function sectionHeader(nr, titel) {
  // Lime blok links, cijfer, dan titel
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: TableBorders.NONE,
    rows: [new TableRow({
      children: [
        // Nummerbadge
        new TableCell({
          children: [new Paragraph({
            children: [t(String(nr), { bold: true, size: 20, color: DARK })],
            alignment: AlignmentType.CENTER,
            spacing: { after: 0 },
          })],
          shading: { fill: LIME, type: ShadingType.CLEAR, color: "auto" },
          verticalAlign: VerticalAlign.CENTER,
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          width: { size: 500, type: WidthType.DXA },
        }),
        // Titeltekst
        new TableCell({
          children: [new Paragraph({
            children: [t(titel, { bold: true, size: 26, color: DARK })],
            spacing: { after: 0 },
          })],
          verticalAlign: VerticalAlign.CENTER,
          margins: { top: 60, bottom: 60, left: 200, right: 120 },
          borders: {
            top:    { style: BorderStyle.NONE },
            right:  { style: BorderStyle.NONE },
            bottom: { style: BorderStyle.SINGLE, size: 4, color: LIME },
            left:   { style: BorderStyle.NONE },
          },
        }),
      ],
    })],
    margins: { top: convertInchesToTwip(0.1), bottom: convertInchesToTwip(0.05) },
  });
}

function subHeader(tekst) {
  return new Paragraph({
    children: [t(tekst, { bold: true, size: 22, color: DARK })],
    spacing: { before: 200, after: 100 },
    border: { left: { style: BorderStyle.THICK, size: 16, color: LIME, space: 8 } },
    indent: { left: convertInchesToTwip(0.15) },
  });
}

// ── SECTIE 1: Voorblad (SVG-stijl cover_C_streetview) ────────────────────────

function maakVoorblad() {
  const TOPBG = "F2F5E8";
  const SVBG  = "E8EDD5";
  const SVGRN = "7A9A50";
  const labelKleur = { A: "2E7D32", B: "558B2F", C: "9E9D24",
                       D: "F57F17", E: "E65100", F: "BF360C", G: "B71C1C" };
  const lk = labelKleur[data.energielabel] ?? MID;

  function topCel(inhoud, bg, opts) {
    opts = opts || {};
    return new TableCell({
      children: inhoud,
      shading: { fill: bg, type: ShadingType.CLEAR, color: "auto" },
      verticalAlign: VerticalAlign.CENTER,
      margins: opts.margins || { top: 0, bottom: 0, left: 0, right: 0 },
      width: opts.width,
      borders: {
        top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
        left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      },
    });
  }

  const noBorder = {
    top:    { style: BorderStyle.NONE },
    bottom: { style: BorderStyle.NONE },
    left:   { style: BorderStyle.NONE },
    right:  { style: BorderStyle.NONE },
  };

  const splitBorder = {
    top:    { style: BorderStyle.NONE },
    bottom: { style: BorderStyle.NONE },
    left:   { style: BorderStyle.NONE },
    right:  { style: BorderStyle.SINGLE, size: 2, color: "EEEEEE" },
  };

  return [
    // 1. Dunne lime accent-lijn bovenaan
    new Paragraph({
      children: [t("", { size: 2 })],
      border: { top: { style: BorderStyle.SINGLE, size: 18, color: LIME, space: 0 } },
      spacing: { after: 0, before: 0 },
    }),

    // 2. Header: PandIQ WONEN + subtitels
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: TableBorders.NONE,
      rows: [new TableRow({
        children: [
          topCel([new Paragraph({
            children: [
              t("PandIQ", { size: 48, bold: true, color: DARK }),
              t("  WONEN", { size: 28, bold: false, color: "999999" }),
            ],
            spacing: { after: 0 },
          })], TOPBG, { margins: { top: convertInchesToTwip(0.22), bottom: convertInchesToTwip(0.15), left: convertInchesToTwip(0.1), right: 80 } }),
          topCel([
            new Paragraph({ children: [t("Isolatie Quickscan", { size: 15, color: "AAAAAA" })], alignment: AlignmentType.RIGHT, spacing: { after: 40 } }),
            new Paragraph({ children: [t("Energierapport verduurzaming", { size: 15, color: "AAAAAA" })], alignment: AlignmentType.RIGHT, spacing: { after: 0 } }),
          ], TOPBG, { margins: { top: convertInchesToTwip(0.22), bottom: convertInchesToTwip(0.15), left: 80, right: convertInchesToTwip(0.1) } }),
        ],
      })],
    }),

    // 3. Street View placeholder box
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
            new Paragraph({ children: [t(data.adres, { size: 16, color: "BBBBBB" })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
          ],
          shading: { fill: SVBG, type: ShadingType.CLEAR, color: "auto" },
          verticalAlign: VerticalAlign.CENTER,
          margins: { top: 0, bottom: 0, left: 0, right: 0 },
          borders: noBorder,
        })],
      })],
    }),

    // 4. Lime separator-band
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
      children: [t("Helper Weststraat 42", { bold: true, size: 36, color: DARK })],
      spacing: { after: 80 },
    }),
    new Paragraph({
      children: [
        t("9721BS Groningen", { size: 22, color: "888888" }),
        t("  \u00B7  ", { size: 22, color: "CCCCCC" }),
        t(data.datum, { size: 22, color: "888888" }),
      ],
      spacing: { after: 0 },
    }),

    // Scheidingslijn
    new Paragraph({
      children: [t("", { size: 2 })],
      border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "EEEEEE", space: 4 } },
      spacing: { before: 120, after: 140 },
    }),

    // 6. Data-cards (4 kolommen)
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: TableBorders.NONE,
      rows: [new TableRow({ children: [

        // Card 1: Energielabel
        new TableCell({
          children: [
            new Paragraph({ children: [t("Energielabel", { size: 16, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
            new Paragraph({
              children: [t("  " + data.energielabel + "  ", { bold: true, size: 28, color: WHITE })],
              alignment: AlignmentType.CENTER, spacing: { after: 0 },
              shading: { fill: lk, type: ShadingType.CLEAR, color: "auto" },
            }),
          ],
          shading: { fill: "F7FAF0", type: ShadingType.CLEAR, color: "auto" },
          margins: { top: 120, bottom: 120, left: 80, right: 80 },
          borders: splitBorder,
        }),

        // Card 2: Bouwjaar
        new TableCell({
          children: [
            new Paragraph({ children: [t("Bouwjaar", { size: 16, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
            new Paragraph({ children: [t(String(data.bouwjaar), { bold: true, size: 32, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
          ],
          shading: { fill: "F7FAF0", type: ShadingType.CLEAR, color: "auto" },
          margins: { top: 120, bottom: 120, left: 80, right: 80 },
          borders: splitBorder,
        }),

        // Card 3: Warmtebehoefte
        new TableCell({
          children: [
            new Paragraph({ children: [t("Warmtebehoefte", { size: 16, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
            new Paragraph({ children: [t(Math.round(data.warmtebehoefte) + " kWh", { bold: true, size: 28, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 20 } }),
            new Paragraph({ children: [t("per m\u00B2/jaar", { size: 15, color: "888888" })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
          ],
          shading: { fill: "F7FAF0", type: ShadingType.CLEAR, color: "auto" },
          margins: { top: 120, bottom: 120, left: 80, right: 80 },
          borders: splitBorder,
        }),

        // Card 4: ISDE-subsidie (lime)
        new TableCell({
          children: [
            new Paragraph({ children: [t("ISDE-subsidie", { size: 16, color: "3A3A3A" })], alignment: AlignmentType.CENTER, spacing: { after: 40 } }),
            new Paragraph({ children: [t("tot " + eur(data.totaal_subsidie), { bold: true, size: 28, color: DARK })], alignment: AlignmentType.CENTER, spacing: { after: 20 } }),
            new Paragraph({ children: [t("indicatief", { size: 15, color: "555555" })], alignment: AlignmentType.CENTER, spacing: { after: 0 } }),
          ],
          shading: { fill: LIME, type: ShadingType.CLEAR, color: "auto" },
          margins: { top: 120, bottom: 120, left: 80, right: 80 },
          borders: noBorder,
        }),

      ]})],
    }),

    // Scheidingslijn
    new Paragraph({
      children: [t("", { size: 2 })],
      border: { top: { style: BorderStyle.SINGLE, size: 2, color: "EEEEEE", space: 4 } },
      spacing: { before: 100, after: 100 },
    }),

    // 7. Footer-regels
    new Paragraph({
      children: [t(data.woningtype + "  \u00B7  " + data.oppervlakte + " m\u00B2  \u00B7  " + data.bouwperiode, { size: 18, color: "AAAAAA" })],
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

    // Pagina-einde
    new Paragraph({ children: [new PageBreak()], spacing: { after: 0 } }),
  ];
}

function maakInterpretatie() {
  const bj = data.bouwjaar;
  const wt = data.woningtype.toLowerCase();
  const el = data.energielabel;

  let context;
  if (bj < 1945) {
    context = `Dit ${wt} is gebouwd voor de Tweede Wereldoorlog (${bj}). In deze periode werd nauwelijks geïsoleerd: muren, dak en vloer zijn vaak thermisch zwak. Er is doorgaans veel verbeterpotentieel.`;
  } else if (bj < 1975) {
    context = `Dit ${wt} stamt uit de wederopbouwperiode (${bj}). Isolatie was beperkt of afwezig. Spouwmuren zijn aanwezig maar zelden gevuld. Er is substantieel verbeterpotentieel.`;
  } else {
    context = `Dit ${wt} is gebouwd in ${bj}. Enige basisinstallatie is aanwezig, maar verbetering is vaak nog goed rendabel.`;
  }

  const labelTxt = {
    A: "uitstekende prestaties", B: "goede prestaties", C: "redelijke prestaties",
    D: "matige prestaties", E: "slechte prestaties", F: "zeer slechte prestaties", G: "extreem slechte prestaties",
  }[el] ?? "onbekende prestaties";

  return [
    sectionHeader(1, "Interpretatie en context"),
    lege(),
    p(context, { after: 140, color: MID }),
    p([
      t(`Het geregistreerde energielabel is `, { size: 20, color: MID }),
      t(el, { size: 20, bold: true, color: DARK }),
      t(` (${labelTxt}). De warmtebehoefte bedraagt `, { size: 20, color: MID }),
      t(`${data.warmtebehoefte} kWh/m²/jaar`, { size: 20, bold: true, color: DARK }),
      t(`. Gerichte isolatiemaatregelen kunnen dit terugdringen.`, { size: 20, color: MID }),
    ], { after: 140 }),
    p(
      "De analyse hierna geeft per bouwdeel de kansen, investeringen, subsidies en terugverdientijden.",
      { after: 0, color: MID }
    ),
    lege(),
  ];
}

// ── SECTIE 3: Woninggegevens ──────────────────────────────────────────────────

function maakWoninggegevens() {
  const rijen = [
    ["Adres",            data.adres],
    ["Bouwjaar",         String(data.bouwjaar)],
    ["Bouwperiode",      data.bouwperiode],
    ["Oppervlakte",      `${data.oppervlakte} m²`],
    ["Woningtype",       data.woningtype],
    ["Energielabel",     data.energielabel],
    ["Energiebehoefte",  `${data.energiebehoefte} kWh/m²/jaar`],
    ["Warmtebehoefte",   `${data.warmtebehoefte} kWh/m²/jaar`],
  ];

  return [
    sectionHeader(2, "Woninggegevens"),
    lege(),
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: dunneRanden(),
      rows: [
        new TableRow({
          children: [
            cel("Kenmerk", { bold: true, bg: LIME, size: 18 }),
            cel("Waarde",  { bold: true, bg: LIME, size: 18 }),
          ],
          tableHeader: true,
        }),
        ...rijen.map((r, i) => new TableRow({ children: [
          cel(r[0], { bold: true,  bg: i % 2 === 0 ? WHITE : LIGHT, size: 18 }),
          cel(r[1], { bold: false, bg: i % 2 === 0 ? WHITE : LIGHT, size: 18, color: MID }),
        ]})),
      ],
    }),
    lege(),
  ];
}

// ── SECTIE 4: Kenmerken bouwperiode ──────────────────────────────────────────

function maakBouwperiode() {
  const bj = data.bouwjaar;
  let kenmerken;

  if (bj < 1945) {
    kenmerken = [
      "Massief metselwerk of half-steens muren zonder spouw. Gevelisolatie van buiten of binnen is noodzakelijk.",
      "Geen of minimale dakisolatie. De zolderverdieping is thermisch zwak.",
      "Houten vloer op kruipruimte. Vloerisolatie met mineraalwol of gespoten PUR is goed mogelijk.",
      "Enkel glas of zeer oud dubbelglas. Vervanging naar HR++ of triple levert direct comfortverbetering.",
      "Geen mechanische ventilatie. Kierdichting vraagt extra aandacht voor vochtveiligheid.",
      "Welstandseisen en monumentenstatus kunnen uitvoering aan de buitenzijde beperken.",
    ];
  } else if (bj < 1975) {
    kenmerken = [
      "Spouwmuur aanwezig maar veelal niet gevuld. Spouwmuurisolatie is doorgaans de meest rendabele maatregel.",
      "Dakisolatie ontbreekt of is minimaal aanwezig.",
      "Houten of betonnen begane grondvloer. Vloerisolatie van onder is mogelijk.",
      "Enkel glas of gewoon dubbelglas. Vervanging naar HR++ of triple is aanbevolen.",
    ];
  } else {
    kenmerken = [
      "Basisspouwmuurisolatie aanwezig. Kwaliteit en dikte kunnen verbetering vragen.",
      "Dakisolatie aanwezig maar mogelijk niet aan huidige normen.",
      "Glas veelal gewoon of HR dubbelglas. Upgrade naar HR++ of triple kan lonen.",
    ];
  }

  return [
    sectionHeader(3, "Kenmerken bouwperiode"),
    lege(),
    p(`Woningen gebouwd ${data.bouwperiode} hebben specifieke bouwkundige kenmerken die de keuze van maatregelen bepalen:`,
      { after: 120, color: MID }),
    ...kenmerken.map((k) => new Paragraph({
      children: [
        t("◆  ", { bold: true, size: 18, color: LIME }),
        t(k, { size: 18, color: MID }),
      ],
      spacing: { after: 80 },
    })),
    lege(),
  ];
}

// ── SECTIE 5: Kansen en verbeterpotentieel ────────────────────────────────────

function maakKansen() {
  const blokken = [
    sectionHeader(4, "Kansen en verbeterpotentieel"),
    lege(),
    p("Per bouwdeel vindt u hieronder de aanbevolen maatregel met indicatieve kosten, subsidie en terugverdientijd.",
      { after: 160, color: MID }),
  ];

  // ── Per maatregel: kaartachtig blok ────────────────────────────────────
  for (const m of data.maatregelen) {
    const filled = "●".repeat(m.score);
    const empty  = "○".repeat(5 - m.score);

    blokken.push(new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: volleRanden(),
      rows: [
        // Koptegel: onderdeel + score
        new TableRow({
          children: [
            new TableCell({
              children: [new Paragraph({
                children: [
                  t(m.onderdeel.toUpperCase(), { bold: true, size: 22, color: DARK }),
                  t(`   ${filled}${empty}   score ${m.score}/5`, { size: 18, color: DARK }),
                ],
                spacing: { after: 0 },
              })],
              shading: { fill: LIME, type: ShadingType.CLEAR, color: "auto" },
              verticalAlign: VerticalAlign.CENTER,
              margins: { top: 100, bottom: 100, left: 160, right: 160 },
              columnSpan: 2,
            }),
          ],
        }),
        // Detailrijen
        ...([
          ["Aanbevolen maatregel",      m.naam],
          ["Geschatte oppervlakte",     `ca. ${m.oppervlakte} m²`],
          ["Indicatieve besparing",     `${eur(m.besparing_min)} tot ${eur(m.besparing_max)} per jaar`],
          ["Indicatieve investering",   `${eur(m.investering_min)} tot ${eur(m.investering_max)}`],
          ["ISDE-subsidie (indicatief)",`tot ${eur(m.subsidie)}`],
          ["Terugverdientijd",          `circa ${m.terugverdientijd}`],
        ].map((r, i) => new TableRow({ children: [
          cel(r[0], { bold: true, bg: i % 2 === 0 ? WHITE : LIGHT, size: 18 }),
          cel(r[1], { bg: i % 2 === 0 ? WHITE : LIGHT, size: 18, color: MID }),
        ]}))),
      ],
    }));

    blokken.push(lege());
  }

  // ── Totaalplaatje ───────────────────────────────────────────────────────
  blokken.push(subHeader("Totaalplaatje: alle maatregelen gecombineerd"));
  blokken.push(p("Als u alle maatregelen uitvoert, ontstaat het volgende totaalplaatje:",
    { after: 100, color: MID }));

  const netto_min = Math.max(0, data.totaal_investering_min - data.totaal_subsidie);
  const netto_max = Math.max(0, data.totaal_investering_max - data.totaal_subsidie);

  blokken.push(new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: volleRanden(),
    rows: [
      new TableRow({
        children: [
          cel("",    { bold: true, bg: LIME, size: 18 }),
          cel("Min", { bold: true, bg: LIME, size: 18, align: AlignmentType.RIGHT }),
          cel("Max", { bold: true, bg: LIME, size: 18, align: AlignmentType.RIGHT }),
        ],
        tableHeader: true,
      }),
      ...([
        ["Totale investering",           eur(data.totaal_investering_min), eur(data.totaal_investering_max)],
        ["ISDE-subsidie (indicatief)",   "-",                              eur(data.totaal_subsidie)],
        ["Netto investering na subsidie",eur(netto_min),                   eur(netto_max)],
        ["Jaarlijkse besparing",         eur(data.totaal_besparing_min),   eur(data.totaal_besparing_max)],
        ["Terugverdientijd",             `${data.terugverdientijd_min} jaar`, `${data.terugverdientijd_max} jaar`],
      ].map((r, i) => new TableRow({ children: [
        cel(r[0], { bold: true, bg: i % 2 === 0 ? WHITE : LIGHT, size: 18 }),
        cel(r[1], { bg: i % 2 === 0 ? WHITE : LIGHT, size: 18, align: AlignmentType.RIGHT, color: MID }),
        cel(r[2], { bg: i % 2 === 0 ? WHITE : LIGHT, size: 18, align: AlignmentType.RIGHT, color: MID }),
      ]}))),
    ],
  }));

  blokken.push(lege());
  blokken.push(p([
    t("Tip: ", { bold: true, size: 17, color: DARK }),
    t("combineer isolatie met een warmtepomp of zonneboiler voor het dubbele ISDE-subsidietarief.",
      { size: 17, italic: true, color: MID }),
  ], { after: 0 }));
  blokken.push(lege());

  return blokken;
}

// ── SECTIE 6: Aandachtspunten en risico's ─────────────────────────────────────

function maakAandachtspunten() {
  const bj = data.bouwjaar;
  const wt = data.woningtype.toLowerCase();

  const punten = [];

  if (bj < 1945) {
    punten.push({ niveau: "Risico",   icon: "⚠",
      tekst: "Kans op condensatie bij binnenisolatie van massief metselwerk. Laat dit vooraf beoordelen door een bouwkundige." });
    punten.push({ niveau: "Let op",   icon: "●",
      tekst: "Welstandseisen kunnen gevelisolatie aan de buitenzijde beperken. Informeer bij uw gemeente voor aanvraag." });
  } else if (bj < 1975) {
    punten.push({ niveau: "Let op",   icon: "●",
      tekst: "Controleer of de spouw minimaal 50 mm breed is. Bij een smallere spouw zijn niet alle materialen geschikt." });
  }

  if (wt === "appartement") {
    punten.push({ niveau: "Risico",   icon: "⚠",
      tekst: "Maatregelen aan de buitenschil (gevel, dak) vereisen doorgaans een VvE-besluit. Bespreek dit tijdig." });
    punten.push({ niveau: "Info",     icon: "ℹ",
      tekst: "Vloerisolatie kan veelal per appartement worden aangevraagd, afhankelijk van het splitsingsreglement." });
  }

  punten.push({ niveau: "Info",       icon: "ℹ",
    tekst: "ISDE-subsidie moet worden aangevraagd voor de start van de werkzaamheden via rvo.nl." });
  punten.push({ niveau: "Info",       icon: "ℹ",
    tekst: "Vraag altijd minimaal twee offertes op bij gecertificeerde isolatiebedrijven." });

  const achtergrond = { Risico: "FDECEA", "Let op": "FFF8E1", Info: LIGHT };
  const randkleur   = { Risico: "C62828", "Let op": "E65100", Info: LIME };

  const blokken = [sectionHeader(5, "Aandachtspunten en risico's"), lege()];

  for (const p_ of punten) {
    blokken.push(new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: TableBorders.NONE,
      rows: [new TableRow({ children: [
        // Gekleurde linkerrand als smalle cel
        new TableCell({
          children: [lege()],
          shading: { fill: randkleur[p_.niveau], type: ShadingType.CLEAR, color: "auto" },
          width: { size: 100, type: WidthType.DXA },
          margins: { top: 0, bottom: 0, left: 0, right: 0 },
        }),
        // Inhoud
        new TableCell({
          children: [new Paragraph({
            children: [
              t(`${p_.niveau}  `, { bold: true, size: 18, color: DARK }),
              t(p_.tekst, { size: 18, color: MID }),
            ],
            spacing: { after: 0 },
          })],
          shading: { fill: achtergrond[p_.niveau], type: ShadingType.CLEAR, color: "auto" },
          margins: { top: 100, bottom: 100, left: 160, right: 120 },
        }),
      ]})],
    }));
    blokken.push(lege());
  }

  return blokken;
}

// ── SECTIE 7: Subsidiebedragen ────────────────────────────────────────────────

function maakSubsidietabel() {
  const rijen = data.maatregelen.map((m, i) => ({
    naam: m.naam,
    opp:  `ca. ${m.oppervlakte} m²`,
    sub:  `tot ${eur(m.subsidie)}`,
    eis:  m.onderdeel === "Glas" ? "U ≤ 1,2 W/m²K" : "Rc ≥ 3,5 m²K/W",
    bg:   i % 2 === 0 ? WHITE : LIGHT,
  }));

  return [
    sectionHeader(6, "Subsidiemogelijkheden (ISDE 2026)"),
    lege(),
    p(`Op basis van uw woning (${data.oppervlakte} m², bouwjaar ${data.bouwjaar}) zijn de volgende ` +
      "ISDE-subsidies indicatief van toepassing:",
      { after: 120, color: MID }),
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: dunneRanden(),
      rows: [
        new TableRow({
          children: [
            cel("Maatregel",    { bold: true, bg: LIME, size: 18 }),
            cel("Oppervlakte",  { bold: true, bg: LIME, size: 18 }),
            cel("Subsidie",     { bold: true, bg: LIME, size: 18, align: AlignmentType.RIGHT }),
            cel("Minimale eis", { bold: true, bg: LIME, size: 18 }),
          ],
          tableHeader: true,
        }),
        ...rijen.map((r) => new TableRow({ children: [
          cel(r.naam, { bg: r.bg, size: 18 }),
          cel(r.opp,  { bg: r.bg, size: 18, color: MID }),
          cel(r.sub,  { bg: r.bg, size: 18, color: MID, align: AlignmentType.RIGHT }),
          cel(r.eis,  { bg: r.bg, size: 18, color: MID }),
        ]})),
        new TableRow({ children: [
          cel("Totaal indicatief",          { bold: true, bg: LIGHT, size: 18 }),
          cel("",                           { bg: LIGHT, size: 18 }),
          cel(`tot ${eur(data.totaal_subsidie)}`, { bold: true, bg: LIGHT, size: 18, align: AlignmentType.RIGHT }),
          cel("",                           { bg: LIGHT, size: 18 }),
        ]}),
      ],
    }),
    lege(),
    p([
      t("Meervoudig tarief: ", { bold: true, size: 17 }),
      t("combineer een isolatiemaatregel met een warmtepomp, zonneboiler of warmtenet voor verdubbeld subsidiebedrag. " +
        "Aanvraag binnen 24 maanden na de eerste maatregel via rvo.nl.",
        { size: 17, color: MID }),
    ], { after: 0 }),
    lege(),
  ];
}

// ── SECTIE 8: Vervolgstappen ──────────────────────────────────────────────────

function maakVervolgstappen() {
  const stappen = [
    ["Bereken uw subsidie",       "Gebruik de ISDE-subsidiecheck op rvo.nl voor uw persoonlijke aanspraak."],
    ["Vraag offertes op",         "Neem contact op met minimaal twee gecertificeerde isolatiebedrijven."],
    ["Plan de volgorde",          "Combineer gevel en dak in één bouwstroom om op steigerkosten te besparen."],
    ["Dien subsidie in voor start","ISDE moet worden aangevraagd voor aanvang van de werkzaamheden."],
    ["Laat een maatwerkadvies maken","Een erkend energieadviseur brengt uw specifieke situatie in kaart."],
  ];

  return [
    sectionHeader(7, "Vervolgstappen"),
    lege(),
    ...stappen.map(([kop, tekst], i) => new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: TableBorders.NONE,
      rows: [new TableRow({ children: [
        // Stapnummer
        new TableCell({
          children: [new Paragraph({
            children: [t(String(i + 1), { bold: true, size: 18, color: DARK })],
            alignment: AlignmentType.CENTER,
            spacing: { after: 0 },
          })],
          shading: { fill: LIME, type: ShadingType.CLEAR, color: "auto" },
          verticalAlign: VerticalAlign.CENTER,
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          width: { size: 400, type: WidthType.DXA },
        }),
        // Tekst
        new TableCell({
          children: [new Paragraph({
            children: [
              t(kop + ". ", { bold: true, size: 18, color: DARK }),
              t(tekst, { size: 18, color: MID }),
            ],
            spacing: { after: 0 },
          })],
          verticalAlign: VerticalAlign.CENTER,
          margins: { top: 80, bottom: 80, left: 160, right: 120 },
        }),
      ]})],
      margins: { bottom: convertInchesToTwip(0.07) },
    })),

    lege(),

    // CTA-blok
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: TableBorders.NONE,
      rows: [new TableRow({ children: [new TableCell({
        children: [
          new Paragraph({
            children: [t("Hulp nodig bij de volgende stap?", { bold: true, size: 24, color: DARK })],
            spacing: { after: 80 },
          }),
          new Paragraph({
            children: [t(
              "PandIQ WONEN helpt u met een persoonlijk energieadvies, het vergelijken van offertes " +
              "en het aanvragen van subsidies.",
              { size: 18, color: DARK }
            )],
            spacing: { after: 80 },
          }),
          new Paragraph({
            children: [t("pandiq.nl", { bold: true, size: 18, color: DARK })],
            spacing: { after: 0 },
          }),
        ],
        shading: { fill: LIME, type: ShadingType.CLEAR, color: "auto" },
        margins: { top: convertInchesToTwip(0.3), bottom: convertInchesToTwip(0.3),
                   left: convertInchesToTwip(0.4), right: convertInchesToTwip(0.4) },
      })],
    })],
    }),

    lege(),
    p([t(
      "Disclaimer: indicatieve quickscan op basis van openbare brondata. Financiële indicaties zijn schattingen. " +
      "PandIQ is niet aansprakelijk voor beslissingen zonder nader onderzoek ter plaatse.",
      { size: 14, italic: true, color: MID }
    )], { after: 0 }),
  ];
}

// ── Document samenstellen ─────────────────────────────────────────────────────

// ── Template vullen ───────────────────────────────────────────────────────────

function vulCoverTemplate() {
  const templatePad = path.join(__dirname, "..", "templates", "cover_template.docx");

  if (!fs.existsSync(templatePad)) {
    console.warn("cover_template.docx niet gevonden — voorblad via code gegenereerd.");
    return null;
  }

  const zip = new PizZip(fs.readFileSync(templatePad, "binary"));
  const doc = new Docxtemplater(zip, { paragraphLoop: true, linebreaks: true });

  // Splits adres in straat en postcode+plaats
  const adresDelen  = data.adres.split(",");
  const straat      = adresDelen[0]?.trim() ?? data.adres;
  const plaatsDeel  = adresDelen[1]?.trim() ?? "";
  const [postcode, ...plaatsArr] = plaatsDeel.split(" ").filter(Boolean);
  const postcode_plaats = plaatsDeel || data.adres;

  doc.render({
    adres:            data.adres,
    straat:           straat,
    postcode_plaats:  postcode_plaats,
    datum:            data.datum,
    energielabel:     data.energielabel,
    bouwjaar:         String(data.bouwjaar),
    warmtebehoefte:   String(Math.round(data.warmtebehoefte)),
    subsidie_totaal:  Math.round(data.totaal_subsidie).toLocaleString("nl-NL"),
    woningtype:       data.woningtype,
    oppervlakte:      String(data.oppervlakte),
    bouwperiode:      data.bouwperiode,
  });

  return doc.getZip().generate({ type: "nodebuffer" });
}

// ── Twee docx-bestanden samenvoegen ───────────────────────────────────────────
// Voegt de <w:body> inhoud van coverBuffer vóór het body van reportBuffer.

function samenvoegen(coverBuffer, reportBuffer) {
  const coverZip  = new PizZip(coverBuffer);
  const reportZip = new PizZip(reportBuffer);

  const coverXml  = coverZip.file("word/document.xml").asText();
  const reportXml = reportZip.file("word/document.xml").asText();

  // Extraheer inhoud binnen <w:body>...</w:body> (zonder sectPr van cover)
  const coverBody  = coverXml.match(/<w:body>([\s\S]*?)<\/w:body>/)?.[1] ?? "";
  const reportBody = reportXml.match(/<w:body>([\s\S]*?)<\/w:body>/)?.[1] ?? "";

  // Verwijder de sectPr van de cover (die zit aan het eind van coverBody)
  const coverBodyClean = coverBody.replace(/<w:sectPr[\s\S]*?<\/w:sectPr>/, "").trimEnd();

  // Bouw nieuwe body: cover + pagina-einde + report
  const paginaEinde = `<w:p><w:r><w:br w:type="page"/></w:r></w:p>`;
  const nieuweBody  = `<w:body>${coverBodyClean}${paginaEinde}${reportBody}</w:body>`;

  // Zet in de report-zip (die heeft alle stijlen/relaties van het gegenereerde rapport)
  const nieuweXml = reportXml.replace(/<w:body>[\s\S]*?<\/w:body>/, nieuweBody);
  reportZip.file("word/document.xml", nieuweXml);

  return reportZip.generate({ type: "nodebuffer", compression: "DEFLATE" });
}

// ── Hoofdfunctie ──────────────────────────────────────────────────────────────

async function genereer() {
  // Body: alle secties behalve het voorblad
  const bodyInhoud = [
    ...maakInterpretatie(),
    ...maakWoninggegevens(),
    ...maakBouwperiode(),
    ...maakKansen(),
    ...maakAandachtspunten(),
    ...maakSubsidietabel(),
    ...maakVervolgstappen(),
  ];

  const bodyDoc = new Document({
    sections: [{
      properties: {
        page: {
          size: { orientation: PageOrientation.PORTRAIT, width: convertInchesToTwip(8.27), height: convertInchesToTwip(11.69) },
          margin: { top: convertInchesToTwip(0.6), bottom: convertInchesToTwip(0.6), left: convertInchesToTwip(0.6), right: convertInchesToTwip(0.6) },
        },
      },
      children: bodyInhoud,
    }],
  });

  const bodyBuffer  = await Packer.toBuffer(bodyDoc);
  const coverBuffer = vulCoverTemplate();

  const eindBuffer = coverBuffer
    ? samenvoegen(coverBuffer, bodyBuffer)
    : await Packer.toBuffer(new Document({
        sections: [{
          properties: { page: { size: { orientation: PageOrientation.PORTRAIT, width: convertInchesToTwip(8.27), height: convertInchesToTwip(11.69) }, margin: { top: convertInchesToTwip(0.6), bottom: convertInchesToTwip(0.6), left: convertInchesToTwip(0.6), right: convertInchesToTwip(0.6) } } },
          children: [...maakVoorblad(), ...bodyInhoud],
        }],
      }));

  const postcode    = "9721BS";
  const huisnummer  = "42";
  const bestandsnaam = `quickscan_${postcode}_${huisnummer}.docx`;
  const outputPad   = path.join(__dirname, "..", "output", bestandsnaam);

  fs.writeFileSync(outputPad, eindBuffer);

  const stats = fs.statSync(outputPad);
  const bron  = coverBuffer ? "cover_template.docx" : "code (geen template gevonden)";
  console.log(`Aangemaakt : ${outputPad}`);
  console.log(`Grootte    : ${(stats.size / 1024).toFixed(1)} kB`);
  console.log(`Voorblad   : ${bron}`);
  console.log("Validatie  : OK");
}

genereer().catch((err) => {
  console.error("Fout:", err);
  process.exit(1);
});
