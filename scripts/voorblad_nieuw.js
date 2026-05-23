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
