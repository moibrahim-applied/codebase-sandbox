"use strict";

const express = require("express");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
const pinoHttp = require("pino-http");

const logger = require("./logger");
const { renderReportPDF } = require("./pdf");
const { ReportRequest } = require("./schema");

const PORT = Number(process.env.PORT || 3000);
const VERSION = require("../package.json").version;

const app = express();

app.use(helmet({ contentSecurityPolicy: false }));
app.use(express.json({ limit: "1mb" }));
app.use(pinoHttp({ logger }));
app.use(
  rateLimit({
    windowMs: 60_000,
    limit: 120,
    standardHeaders: true,
    legacyHeaders: false,
  }),
);

app.get("/", (_req, res) => {
  res.json({
    service: "report-service",
    product: "FreeWeigh.Net",
    version: VERSION,
    compliance: ["ALCOA+", "CFR-21-Part-11", "GWP"],
  });
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok", version: VERSION });
});

app.post("/reports/release", async (req, res) => {
  const parsed = ReportRequest.safeParse(req.body);
  if (!parsed.success) {
    return res.status(422).json({ error: "validation_failed", details: parsed.error.flatten() });
  }
  const pdf = await renderReportPDF(parsed.data);
  res.setHeader("Content-Type", "application/pdf");
  res.setHeader("Content-Disposition", `attachment; filename="release-${parsed.data.releaseId}.pdf"`);
  res.send(pdf);
});

app.use((err, _req, res, _next) => {
  logger.error({ err }, "unhandled");
  res.status(500).json({ error: "internal_error" });
});

if (require.main === module) {
  app.listen(PORT, () => logger.info({ port: PORT }, "report-service listening"));
}

module.exports = app;
