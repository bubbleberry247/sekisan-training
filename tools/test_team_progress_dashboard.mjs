import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const apiSource = fs.readFileSync(new URL('../src/api.gs', import.meta.url), 'utf8');
const functionStart = apiSource.indexOf('function buildTeamProgressSummary_(');
assert.ok(functionStart >= 0, 'buildTeamProgressSummary_ must exist');
const openingBrace = apiSource.indexOf('{', functionStart);
let depth = 0;
let functionEnd = openingBrace;
let quote = '';
let escaped = false;
for (; functionEnd < apiSource.length; functionEnd += 1) {
  const char = apiSource[functionEnd];
  if (quote) {
    if (escaped) escaped = false;
    else if (char === '\\') escaped = true;
    else if (char === quote) quote = '';
    continue;
  }
  if (char === '"' || char === "'" || char === '`') {
    quote = char;
    continue;
  }
  if (char === '{') depth += 1;
  if (char === '}' && --depth === 0) {
    functionEnd += 1;
    break;
  }
}
const source = apiSource.slice(functionStart, functionEnd);
const context = {
  console,
  Logger: { log() {} },
  normalizeUserAccessBoolean_(value, defaultValue) {
    if (value === true || value === false) return value ? 'true' : 'false';
    const raw = String(value ?? '').trim().toLowerCase();
    if (!raw) return defaultValue ? 'true' : 'false';
    return ['false', '0', 'no'].includes(raw) ? 'false' : 'true';
  },
  buildProgress_(attempts, totalTests) {
    return {
      attemptsTotal: attempts.length,
      submittedTests: 0,
      totalTests,
    };
  },
};
vm.createContext(context);
vm.runInContext(source, context);

const rows = [
  { email: ' Admin@Example.com ', role: 'ADMIN', active: 'false', showInDashboard: 'false', managerEmail: 'other@example.com', displayName: 'Admin' },
  { email: 'manager@example.com', role: 'manager', active: true, showInDashboard: true, managerEmail: '', displayName: 'Manager' },
  { email: 'direct@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: ' MANAGER@EXAMPLE.COM ', displayName: 'Direct' },
  { email: 'DIRECT-HIDDEN@example.com', role: 'user', active: true, showInDashboard: false, managerEmail: 'manager@example.com', displayName: 'Hidden direct' },
  { email: 'inactive@example.com', role: 'user', active: false, showInDashboard: true, managerEmail: 'manager@example.com', displayName: 'Inactive' },
  { email: 'other-manager@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: 'other-manager@example.com', displayName: 'Non-direct' },
  { email: 'user@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: '', displayName: 'User' },
];

const userRows = rows.map((row, index) => ({
  email: row.email,
  userKey: `key-${index}`,
  displayName: row.displayName,
}));
const attempts = userRows.map((row, index) => ({ userKey: row.userKey, status: index === 0 ? 'submitted' : 'started' }));

function emails(viewer) {
  return Array.from(context.buildTeamProgressSummary_(rows, userRows, attempts, 16, 'Asia/Tokyo', viewer)
    .team, (member) => member.email);
}

function emailsFrom(accessRows, viewer) {
  const accessUsers = accessRows.map((row, index) => ({
    email: row.email,
    userKey: `access-key-${index}`,
    displayName: row.displayName,
  }));
  return Array.from(context.buildTeamProgressSummary_(accessRows, accessUsers, [], 16, 'Asia/Tokyo', viewer)
    .team, (member) => member.email);
}

// Admin sees the existing active/visible population plus themself, even when
// their own access row is inactive/hidden or has an unrelated manager.
assert.deepEqual(emails({ role: ' ADMIN ', email: ' ADMIN@EXAMPLE.COM ' }), [
  'admin@example.com',
  'manager@example.com',
  'direct@example.com',
  'other-manager@example.com',
  'user@example.com',
]);

// Manager sees themself plus active/visible direct reports only.  Email and
// managerEmail matching must ignore surrounding whitespace and case.
assert.deepEqual(emails({ role: 'MANAGER', email: ' Manager@Example.com ' }), [
  'manager@example.com',
  'direct@example.com',
]);

// The manager's own row is included even when its access flags and manager
// reference are stale; this exception must not leak to other rows.
const staleManagerRows = rows.map((row) => row.email.trim().toLowerCase() === 'manager@example.com'
  ? { ...row, active: false, showInDashboard: false, managerEmail: 'unrelated@example.com' }
  : row);
assert.deepEqual(emailsFrom(staleManagerRows, { role: 'manager', email: ' MANAGER@EXAMPLE.COM ' }), [
  'manager@example.com',
  'direct@example.com',
]);

// A normal user never receives a team summary, including their own row.
assert.deepEqual(emails({ role: 'user', email: ' user@example.com ' }), []);

// The self exception is limited to admin/manager; no accidental inclusion of
// inactive/hidden/non-direct other users is allowed.
const managerSummary = context.buildTeamProgressSummary_(rows, userRows, attempts, 16, 'Asia/Tokyo', {
  role: 'manager', email: 'manager@example.com',
});
assert.equal(managerSummary.team.some((member) => member.email === 'inactive@example.com'), false);
assert.equal(managerSummary.team.some((member) => member.email === 'DIRECT-HIDDEN@example.com'), false);
assert.equal(managerSummary.team.some((member) => member.email === 'other-manager@example.com'), false);

// A zero-attempt member is still visible and receives a zero-progress object.
const zeroRows = [{ email: 'zero@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: 'manager@example.com', displayName: 'Zero' }];
const zeroUserRows = [{ email: 'zero@example.com', userKey: 'zero-key', displayName: 'Zero' }];
const zeroSummary = context.buildTeamProgressSummary_(
  [{ email: 'manager@example.com', role: 'manager', active: true, showInDashboard: true }, ...zeroRows],
  [{ email: 'manager@example.com', userKey: 'manager-key', displayName: 'Manager' }, ...zeroUserRows],
  [],
  16,
  'Asia/Tokyo',
  { role: 'manager', email: 'MANAGER@EXAMPLE.COM' },
);
const zeroMember = zeroSummary.team.find((member) => member.email === 'zero@example.com');
assert.ok(zeroMember);
assert.equal(zeroMember.progress.attemptsTotal, 0);
assert.equal(zeroMember.progress.totalTests, 16);

// Duplicate self rows that differ only by case/whitespace still produce one row.
const duplicateSelfRows = [
  { email: ' ADMIN@EXAMPLE.COM ', role: 'admin', active: false, showInDashboard: false, displayName: 'Admin hidden' },
  { email: 'admin@example.com', role: 'admin', active: true, showInDashboard: true, displayName: 'Admin visible' },
  { email: 'other@example.com', role: 'user', active: true, showInDashboard: true, displayName: 'Other' },
];
assert.deepEqual(emailsFrom(duplicateSelfRows, { role: 'admin', email: ' admin@example.com ' }), [
  'admin@example.com',
  'other@example.com',
]);

// Other users are deduplicated after row-level eligibility.  Hidden duplicates
// neither hide an eligible row nor create a second row, and the first eligible
// occurrence determines the stable display order.
const duplicateOtherRows = [
  { email: 'viewer@example.com', role: 'admin', active: true, showInDashboard: true, displayName: 'Viewer' },
  { email: ' BETA@example.com ', role: 'user', active: true, showInDashboard: true, displayName: 'Beta first' },
  { email: 'alpha@example.com', role: 'user', active: true, showInDashboard: true, displayName: 'Alpha' },
  { email: 'beta@example.com', role: 'user', active: true, showInDashboard: false, displayName: 'Beta hidden duplicate' },
  { email: 'beta@example.com', role: 'user', active: true, showInDashboard: true, displayName: 'Beta visible duplicate' },
];
assert.deepEqual(emailsFrom(duplicateOtherRows, { role: 'admin', email: 'viewer@example.com' }), [
  'viewer@example.com',
  'beta@example.com',
  'alpha@example.com',
]);

// Manager scope is evaluated on each complete physical row before deduplication:
// a non-direct duplicate cannot authorize access, while a later direct and
// otherwise eligible row can be selected exactly once.
const managerConflictRows = [
  { email: 'manager@example.com', role: 'manager', active: true, showInDashboard: true, displayName: 'Manager' },
  { email: 'conflict@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: 'other@example.com', displayName: 'Non-direct duplicate' },
  { email: ' CONFLICT@EXAMPLE.COM ', role: 'user', active: false, showInDashboard: true, managerEmail: 'manager@example.com', displayName: 'Inactive direct duplicate' },
  { email: 'conflict@example.com', role: 'user', active: true, showInDashboard: false, managerEmail: 'manager@example.com', displayName: 'Hidden direct duplicate' },
  { email: 'conflict@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: ' MANAGER@EXAMPLE.COM ', displayName: 'Eligible direct duplicate' },
  { email: 'tail@example.com', role: 'user', active: true, showInDashboard: true, managerEmail: 'manager@example.com', displayName: 'Tail' },
];
assert.deepEqual(emailsFrom(managerConflictRows, { role: 'manager', email: 'manager@example.com' }), [
  'manager@example.com',
  'conflict@example.com',
  'tail@example.com',
]);

console.log('team progress dashboard contracts: 14 assertions passed');
