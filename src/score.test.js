import assert from "node:assert/strict";
import test from "node:test";
import { evaluate, puzzleIndex } from "./score.js";

const epoch = Date.UTC(2026, 10, 21);

test("wins at exactly 5 percent and loses just outside it", () => {
  assert.equal(evaluate(100, 95).win, true);
  assert.equal(evaluate(100, 105).band, "win");
  const under = evaluate(100, 94.99);
  assert.equal(under.win, false);
  assert.equal(under.band, "close");
  assert.equal(under.direction, "higher");
});

test("25 percent is close and just past it is far", () => {
  assert.equal(evaluate(100, 75).band, "close");
  assert.equal(evaluate(100, 125).band, "close");
  assert.equal(evaluate(100, 125).direction, "lower");
  assert.equal(evaluate(100, 74.99).band, "far");
  assert.equal(evaluate(100, 125.01).band, "far");
});

test("rejects empty and zero guesses", () => {
  assert.ok(evaluate(100, 0).error);
  assert.ok(evaluate(100, -5).error);
  assert.ok(evaluate(100, Number.NaN).error);
});

test("launch day is puzzle 1 and the next day advances", () => {
  assert.deepEqual(puzzleIndex("2026-11-21", 160, epoch), { index: 0, number: 1 });
  assert.equal(puzzleIndex("2026-11-22", 160, epoch).number, 2);
  assert.equal(puzzleIndex("2026-11-22", 160, epoch).index, 1);
});
