"use strict";

const { z } = require("zod");

const AuditEntry = z.object({
  id: z.string().min(1),
  kind: z.enum(["weigh", "calibrate"]),
  recordedAt: z.string().datetime(),
  payload: z.record(z.any()),
});

const ReportRequest = z.object({
  releaseId: z.string().min(3).max(64),
  product: z.string().min(2),
  cveIds: z.array(z.string().regex(/^CVE-\d{4}-\d{4,7}$/)).default([]),
  preparedBy: z.string().min(2),
  preparedAt: z.string().datetime(),
  audit: z.array(AuditEntry).max(500).default([]),
  notes: z.string().max(4000).optional(),
});

module.exports = { AuditEntry, ReportRequest };
