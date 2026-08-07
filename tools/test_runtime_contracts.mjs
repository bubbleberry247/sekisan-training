import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const context = {
  console,
  Utilities: {
    parseDate(value) {
      const parsed = new Date(String(value).replace(' ', 'T') + '+09:00');
      if (Number.isNaN(parsed.getTime())) throw new Error('invalid date');
      return parsed;
    },
  },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(new URL('../src/logic.gs', import.meta.url), 'utf8'), context);

const alternativeQuestions = [
  { qId: 'H26sekisan-040', correct: 'B,C' },
  { qId: 'R2sekisan-013', correct: 'B,C' },
];

for (const question of alternativeQuestions) {
  assert.equal(context.getAnswerMode_(question), 'anyOf');
  assert.equal(context.getAnswerCount_(question), 1);
  assert.equal(context.isCorrectAnswer_(question, ['B']), true);
  assert.equal(context.isCorrectAnswer_(question, ['C']), true);
  assert.equal(context.isCorrectAnswer_(question, ['B', 'C']), false);
  assert.equal(context.isCorrectAnswer_(question, ['A']), false);
}

const allOf = { qId: 'synthetic-all-of', correct: 'A,C' };
assert.equal(context.getAnswerMode_(allOf), 'allOf');
assert.equal(context.getAnswerCount_(allOf), 2);
assert.equal(context.isCorrectAnswer_(allOf, ['A', 'C']), true);
assert.equal(context.isCorrectAnswer_(allOf, ['A']), false);

const single = { qId: 'synthetic-single', correct: 'D' };
assert.equal(context.getAnswerMode_(single), 'single');
assert.equal(context.getAnswerCount_(single), 1);
assert.equal(context.isCorrectAnswer_(single, ['D']), true);
assert.equal(context.isCorrectAnswer_(single, ['C']), false);

assert.equal(context.parseDateTime_('', 'Asia/Tokyo'), null);
assert.equal(context.parseDateTime_('not-a-date', 'Asia/Tokyo'), null);
assert.equal(
  context.parseDateTime_('2026-07-28 17:04:46', 'Asia/Tokyo').toISOString(),
  '2026-07-28T08:04:46.000Z',
);
const dateObject = new Date('2026-07-28T08:04:46.000Z');
assert.equal(context.parseDateTime_(dateObject, 'Asia/Tokyo').getTime(), dateObject.getTime());
const now = new Date('2026-07-28T08:04:46.000Z');
assert.equal(context.isAttemptExpired_({ mode: 'test', endsAt: '' }, now, 'Asia/Tokyo'), true);
assert.equal(context.isAttemptExpired_({ mode: 'mock', endsAt: 'invalid' }, now, 'Asia/Tokyo'), true);
assert.equal(context.isAttemptExpired_({ mode: 'field', endsAt: '2026-07-28 18:04:46' }, now, 'Asia/Tokyo'), false);
assert.equal(context.isAttemptExpired_({ mode: 'practice', endsAt: '' }, now, 'Asia/Tokyo'), false);
assert.equal(context.isAttemptExpired_({ mode: 'practice', endsAt: 'invalid' }, now, 'Asia/Tokyo'), true);

const wrongAlternative = context.buildWrongQuestionForClient_(
  {
    qId: 'H26sekisan-040', correct: 'B,C', stem: 'test',
    choiceA: 'A', choiceB: 'B', choiceC: 'C', choiceD: 'D',
  },
  'A',
  'wrong explanation',
);
assert.equal(wrongAlternative.answerMode, 'anyOf');
assert.equal(wrongAlternative.answerCount, 1);

const clientSource = fs.readFileSync(new URL('../src/index.html', import.meta.url), 'utf8');
assert.match(clientSource, /function getAnswerMode\(q\)/);
assert.match(clientSource, /getAnswerMode\(q\) === 'anyOf'/);
assert.match(clientSource, /isCorrectSelection\(q, chosenKeys\)/);

console.log('runtime contracts: 34 assertions passed');
