"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { ReportRequest } = require("../src/schema");

test("accepts a minimal valid request", () => {
  const ok = ReportRequest.safeParse({
    releaseId: "rel-001",
    product: "FreeWeigh.Net",
    preparedBy: "qa-team",
    preparedAt: "2026-05-19T10:00:00Z",
  });
  assert.equal(ok.success, true);
  assert.deepEqual(ok.data.cveIds, []);
  assert.deepEqual(ok.data.audit, []);
});

test("rejects malformed CVE ids", () => {
  const bad = ReportRequest.safeParse({
    releaseId: "rel-001",
    product: "FreeWeigh.Net",
    preparedBy: "qa-team",
    preparedAt: "2026-05-19T10:00:00Z",
    cveIds: ["CVE-2021"],
  });
  assert.equal(bad.success, false);
});

test("caps audit array at 500", () => {
  const many = Array.from({ length: 501 }, (_, i) => ({
    id: `r${i}`,
    kind: "weigh",
    recordedAt: "2026-05-19T10:00:00Z",
    payload: {},
  }));
  const bad = ReportRequest.safeParse({
    releaseId: "rel-001",
    product: "FreeWeigh.Net",
    preparedBy: "qa-team",
    preparedAt: "2026-05-19T10:00:00Z",
    audit: many,
  });
  assert.equal(bad.success, false);
});
