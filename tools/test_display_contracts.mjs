import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const clientSource = fs.readFileSync(new URL('../src/index.html', import.meta.url), 'utf8');
const start = clientSource.indexOf('function escapeHtml');
const end = clientSource.indexOf('function renderQuestionImage');
assert.ok(start >= 0 && end > start, 'display helpers must be present');

const context = { console };
vm.createContext(context);
vm.runInContext(clientSource.slice(start, end), context);

const fixture = JSON.parse(
  fs.readFileSync(new URL('../data/sekisan_question_corrections_20260807.json', import.meta.url), 'utf8'),
);

for (const qId of ['H25sekisan-029', 'H28sekisan-026']) {
  const stem = fixture.corrections[qId].stem;
  const rendered = context.fmtStem(stem, qId);
  const compressed = context.fmtStem(stem, 'synthetic-other-qid');
  assert.match(rendered, /<br><br>/, `${qId}: paragraph break must be preserved`);
  assert.notEqual(rendered, compressed, `${qId}: qId-specific preservation must be active`);
  assert.ok(rendered.includes('<br>'), `${qId}: list/paragraph line breaks must render`);
}

const sourceRow = fixture.corrections['H25sekisan-029'].stem;
assert.equal(sourceRow.includes('\n・'), true, 'H25sekisan-029 fixture must retain bullet line breaks');
assert.equal(
  fixture.corrections['H28sekisan-026'].stem.includes('\n\n製品や'),
  true,
  'H28sekisan-026 fixture must retain the source paragraph break',
);

assert.match(clientSource, /q\.explainLong \|\| q\.explainShort \|\| '解説がありません'/);
console.log('display contracts: 8 assertions passed');
