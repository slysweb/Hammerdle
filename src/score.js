/** Costcodle Classic scoring: win within 5% of the target, warm within 25%. */

export function evaluate(target, guess) {
  if (!Number.isFinite(target) || target <= 0) {
    return { error: "This puzzle has no price." };
  }
  if (!Number.isFinite(guess) || guess <= 0 || guess > 1e15) {
    return { error: "Enter a price in dollars." };
  }
  const percent = (Math.abs(guess - target) / target) * 100;
  const win = percent <= 5;
  const band = win ? "win" : percent <= 25 ? "close" : "far";
  const direction = guess < target ? "higher" : guess > target ? "lower" : "correct";
  return {
    guess,
    percent: Math.round(percent * 10) / 10,
    win,
    band,
    direction,
  };
}

export function puzzleIndex(dateStr, count, epochUtc) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const days = Math.floor((Date.UTC(y, m - 1, d) - epochUtc) / 86400000);
  const index = ((days % count) + count) % count;
  return { index, number: days + 1 };
}
