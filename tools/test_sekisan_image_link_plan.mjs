import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../src/Code.gs", import.meta.url), "utf8");
const start = source.indexOf("function buildSekisanGitHubImageLinkPlan_");
const end = source.indexOf("\nfunction getSekisanGitHubImageFileMap_", start);
assert.ok(start >= 0 && end > start, "image link plan helper must be present");

const sandbox = {
  sekisanImageBaseNameFromQId_(qId) {
    const match = String(qId).match(/^((?:H|R)\d+)sekisan-(\d{3})$/);
    return match ? `sekisan_${match[1]}_${match[2]}` : "";
  },
};
vm.createContext(sandbox);
vm.runInContext(source.slice(start, end), sandbox);

const base = "https://raw.githubusercontent.com/example/repo/main/images/sekisan/";
const data = [
  ["qId", "imageUrl"],
  ["H25sekisan-043", "images/sekisan/sekisan_H25_043.png"],
  ["H25sekisan-044", "images/sekisan/sekisan_H25_044.png"],
  ["H25sekisan-001", ""],
];

const complete = sandbox.buildSekisanGitHubImageLinkPlan_(
  data,
  0,
  1,
  { "sekisan_H25_043.png": true, "sekisan_H25_044.png": true },
  base,
);
assert.deepEqual(Array.from(complete.missing), []);
assert.equal(complete.expected, 2);
assert.equal(complete.updated, 2);
assert.equal(complete.values[0][0], `${base}sekisan_H25_043.png`);
assert.equal(complete.values[1][0], `${base}sekisan_H25_044.png`);
assert.equal(complete.values[2][0], "");

const incomplete = sandbox.buildSekisanGitHubImageLinkPlan_(
  data,
  0,
  1,
  { "sekisan_H25_043.png": true },
  base,
);
assert.deepEqual(Array.from(incomplete.missing), ["H25sekisan-044 (sekisan_H25_044.png)"]);
assert.equal(incomplete.values[1][0], "images/sekisan/sekisan_H25_044.png");

console.log("sekisan image link plan tests: ok");
