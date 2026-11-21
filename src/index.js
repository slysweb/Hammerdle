import puzzles from "./puzzles.json";
import { evaluate, puzzleIndex } from "./score.js";

const EPOCH = Date.UTC(2026, 10, 21);

const PUBLIC_KEYS = [
  "id", "name", "creator", "year", "yearLabel", "category", "priceType", "priceDate",
  "approximate", "venue", "context", "sourceUrl", "image", "imageRights", "imageLicense",
  "imageLicenseUrl", "imageCredit", "imagePage", "imageNote",
];

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function utcToday() {
  return new Date().toISOString().slice(0, 10);
}

function requestedDate(url) {
  const q = url.searchParams.get("date");
  if (q && /^\d{4}-\d{2}-\d{2}$/.test(q)) {
    const [y, m, d] = q.split("-").map(Number);
    const parsed = new Date(Date.UTC(y, m - 1, d));
    if (parsed.getUTCFullYear() === y && parsed.getUTCMonth() === m - 1 && parsed.getUTCDate() === d) {
      return q;
    }
  }
  return utcToday();
}

function select(date) {
  const { index, number } = puzzleIndex(date, puzzles.length, EPOCH);
  return { puzzle: puzzles[index], number };
}

function publicPuzzle(puzzle, number, date) {
  const out = { number, date };
  for (const key of PUBLIC_KEYS) out[key] = puzzle[key] ?? null;
  return out;
}

function parseAmount(value) {
  if (typeof value === "number") return value;
  if (typeof value !== "string") return Number.NaN;
  return Number(value.replace(/[$,\s]/g, ""));
}

async function handleApi(request, url) {
  if (puzzles.length === 0) return json({ error: "No puzzles are loaded." }, 500);
  const date = requestedDate(url);
  const { puzzle, number } = select(date);

  if (url.pathname === "/api/puzzle" && request.method === "GET") {
    return json(publicPuzzle(puzzle, number, date));
  }

  if (url.pathname === "/api/guess" && request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return json({ error: "Enter a price in dollars." }, 400);
    }
    const result = evaluate(puzzle.amount, parseAmount(body.amount));
    if (result.error) return json({ error: result.error }, 400);
    const payload = { ...result };
    if (result.win || body.reveal === true) payload.answer = puzzle.amount;
    return json(payload);
  }

  return json({ error: "Not found." }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) return handleApi(request, url);
    return env.ASSETS.fetch(request);
  },
};
