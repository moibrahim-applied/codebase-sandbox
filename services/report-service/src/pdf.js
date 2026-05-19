"use strict";

const PDFDocument = require("pdfkit");

const BRAND_BLUE = "#244BA6";
const SUCCESS = "#4C9D2F";
const MUTED = "#5a6470";

function renderReportPDF(req) {
  return new Promise((resolve, reject) => {
    try {
      const doc = new PDFDocument({ size: "A4", margin: 48 });
      const chunks = [];
      doc.on("data", (c) => chunks.push(c));
      doc.on("end", () => resolve(Buffer.concat(chunks)));
      doc.on("error", reject);

      doc.fillColor(BRAND_BLUE).fontSize(18).text("Mettler-Toledo", { continued: true })
         .fillColor(MUTED).fontSize(11).text(`   ·   ${req.product}`);
      doc.moveDown(0.5);
      doc.fillColor("#1a1a1a").fontSize(20).text(`Release Report · ${req.releaseId}`);
      doc.moveDown(0.5);
      doc.fillColor(MUTED).fontSize(10).text(
        `Prepared by ${req.preparedBy} on ${req.preparedAt}`,
      );

      if (req.cveIds.length > 0) {
        doc.moveDown(1).fillColor("#1a1a1a").fontSize(13).text("CVEs addressed");
        doc.moveDown(0.3).fontSize(11);
        for (const cve of req.cveIds) doc.text(`  • ${cve}`);
      }

      doc.moveDown(1).fillColor("#1a1a1a").fontSize(13).text("Audit summary");
      doc.moveDown(0.3).fillColor(MUTED).fontSize(10).text(
        `${req.audit.length} record(s) included.`,
      );
      doc.fontSize(9).fillColor("#1a1a1a");
      for (const entry of req.audit.slice(0, 20)) {
        doc.text(`  · [${entry.kind}] ${entry.id} @ ${entry.recordedAt}`);
      }
      if (req.audit.length > 20) {
        doc.moveDown(0.3).fillColor(MUTED).text(`… ${req.audit.length - 20} more record(s) elided in summary.`);
      }

      if (req.notes) {
        doc.moveDown(1).fillColor("#1a1a1a").fontSize(13).text("Notes");
        doc.moveDown(0.3).fontSize(10).text(req.notes);
      }

      doc.moveDown(2).fillColor(SUCCESS).fontSize(10).text(
        "ALCOA+  ·  CFR 21 Part 11  ·  GWP",
        { align: "center" },
      );

      doc.end();
    } catch (e) {
      reject(e);
    }
  });
}

module.exports = { renderReportPDF };
