const MAX = 6;
const form = document.querySelector("#form");
const amountInput = document.querySelector("#amount");
const rowsEl = document.querySelector("#rows");
const counterEl = document.querySelector("#counter");
const statusEl = document.querySelector("#status");
const card = document.querySelector("#card");
const help = document.querySelector("#help");
const statsDialog = document.querySelector("#stats");
const resultDialog = document.querySelector("#result");

const state = {
  puzzle: null,
  guesses: [],
  answer: null,
  finished: false,
  unit: 1_000_000,
};

function storageKey() {
  return `hammerdle:v1:${state.puzzle.date}`;
}

function dollars(n) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function compact(n, divisor, label) {
  const value = Math.round((n / divisor) * 100) / 100;
  const text = Number.isInteger(value) ? String(value) : String(value);
  return `$${text} ${label}`;
}

function money(n) {
  if (n >= 1_000_000) return compact(n, 1_000_000, "million");
  if (n >= 10_000) return compact(n, 1_000, "thousand");
  return dollars(n);
}

function saleLine(puzzle) {
  const year = (puzzle.priceDate || "").slice(0, 4);
  const kind = puzzle.priceType === "private_sale" ? "private-sale" : "auction";
  const about = puzzle.approximate ? "about " : "";
  return year ? `Guess the ${about}${year} ${kind} price` : `Guess the ${about}${kind} price`;
}

function arrow(guess) {
  if (guess.win) return "✓";
  if (guess.direction === "higher") return "↑";
  if (guess.direction === "lower") return "↓";
  return "✓";
}

function describe(guess) {
  const way = guess.direction === "higher" ? "The price is higher." : guess.direction === "lower" ? "The price is lower." : "Correct.";
  const dist = guess.band === "win" ? "Within 5 percent." : guess.band === "close" ? "Within 25 percent." : "More than 25 percent away.";
  return `${money(guess.guess)}. ${way} ${dist}`;
}

function showStatus(message) {
  statusEl.hidden = !message;
  statusEl.textContent = message || "";
}

function renderPuzzle() {
  const puzzle = state.puzzle;
  document.querySelector("#number").textContent = String(puzzle.number);
  const photo = document.querySelector("#photo");
  photo.src = puzzle.image.startsWith("/") ? puzzle.image : `/${puzzle.image}`;
  photo.alt = puzzle.name;
  document.querySelector("#title").textContent = puzzle.name;
  const bits = [puzzle.creator, puzzle.yearLabel].filter(Boolean);
  document.querySelector("#meta").textContent = bits.join(" · ");
  document.querySelector("#prompt").textContent = saleLine(puzzle);
  document.querySelector("#context").textContent = puzzle.context || "";
  const note = document.querySelector("#note");
  note.hidden = !puzzle.imageNote;
  note.textContent = puzzle.imageNote || "";
  document.querySelector("#credit").innerHTML = creditHtml(puzzle);
  card.hidden = false;
}

function creditHtml(puzzle) {
  if (!puzzle.imageCredit && puzzle.imageRights !== "cc_by" && puzzle.imageRights !== "cc_by_sa") return "";
  const credit = escapeHtml(puzzle.imageCredit || "Photographer");
  const license = puzzle.imageLicenseUrl
    ? `<a href="${escapeAttr(puzzle.imageLicenseUrl)}">${escapeHtml(puzzle.imageLicense || "License")}</a>`
    : escapeHtml(puzzle.imageLicense || "");
  const source = puzzle.imagePage ? `<a href="${escapeAttr(puzzle.imagePage)}">Source</a>` : "";
  return [credit, license, source].filter(Boolean).join(" · ");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

function escapeAttr(value) {
  return escapeHtml(value);
}

function renderRows() {
  rowsEl.innerHTML = "";
  for (let i = 0; i < MAX; i += 1) {
    const row = document.createElement("div");
    row.className = "row";
    const guess = state.guesses[i];
    if (guess) {
      row.classList.add(guess.band);
      row.innerHTML = `<span>${escapeHtml(money(guess.guess))}</span><span class="arrow" aria-hidden="true">${arrow(guess)}</span>`;
      row.setAttribute("aria-label", describe(guess));
    } else {
      row.setAttribute("aria-hidden", "true");
    }
    rowsEl.appendChild(row);
  }
  const n = Math.min(state.guesses.length + 1, MAX);
  counterEl.textContent = state.finished ? "DONE" : `GUESS ${n} / ${MAX}`;
  if (state.finished && state.answer != null) {
    document.querySelector("#prompt").textContent = `Sold for ${money(state.answer)}`;
  }
  const locked = state.finished;
  amountInput.disabled = locked;
  form.querySelector(".submit").disabled = locked;
  for (const button of document.querySelectorAll("#units button")) button.disabled = locked;
  updatePreview();
}

function guessDollars() {
  const n = Number(amountInput.value.trim().replace(/[$,\s]/g, ""));
  if (!Number.isFinite(n) || n <= 0) return null;
  const dollars = Math.round(n * state.unit);
  if (!Number.isFinite(dollars) || dollars <= 0 || dollars > 1e15) return null;
  return dollars;
}

function updatePreview() {
  const preview = document.querySelector("#preview");
  const value = guessDollars();
  if (value == null || state.unit === 1) {
    preview.textContent = "";
    return;
  }
  preview.textContent = `= ${dollars(value)}`;
}

function persist() {
  localStorage.setItem(storageKey(), JSON.stringify({
    id: state.puzzle.id,
    guesses: state.guesses,
    answer: state.answer,
    finished: state.finished,
  }));
}

function restore() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey()) || "null");
    if (!saved || saved.id !== state.puzzle.id) return;
    state.guesses = saved.guesses || [];
    state.answer = saved.answer ?? null;
    state.finished = Boolean(saved.finished);
  } catch {
    /* ignore a broken save */
  }
}

async function load() {
  const params = new URLSearchParams(location.search);
  const date = params.get("date");
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  const response = await fetch(`/api/puzzle${query}`);
  if (!response.ok) throw new Error("The daily puzzle did not load.");
  state.puzzle = await response.json();
  restore();
  renderPuzzle();
  renderRows();
  tick();
  if (state.finished) showResult(false);
  else if (!localStorage.getItem("hammerdle:v1:help-seen")) help.showModal();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.finished) return;
  showStatus("");
  const guessed = guessDollars();
  if (guessed == null) {
    showStatus("Enter a price.");
    return;
  }
  const last = state.guesses.length + 1 === MAX;
  const response = await fetch(`/api/guess${location.search && location.search.includes("date=") ? location.search : ""}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ amount: guessed, reveal: last }),
  });
  const data = await response.json();
  if (!response.ok) {
    showStatus(data.error || "That guess did not count.");
    return;
  }
  state.guesses.push(data);
  amountInput.value = "";
  if (data.win || state.guesses.length >= MAX) {
    state.finished = true;
    state.answer = data.answer;
    record(data.win);
    persist();
    renderRows();
    showResult(true);
    return;
  }
  persist();
  renderRows();
  amountInput.focus();
});

function loadStats() {
  try {
    return JSON.parse(localStorage.getItem("hammerdle:v1:stats")) || emptyStats();
  } catch {
    return emptyStats();
  }
}

function emptyStats() {
  return { played: 0, wins: 0, streak: 0, maxStreak: 0, dist: [0, 0, 0, 0, 0, 0], lastDate: null };
}

function previousDate(date) {
  const [y, m, d] = date.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() - 1);
  return dt.toISOString().slice(0, 10);
}

function record(win) {
  const stats = loadStats();
  if (stats.lastDate === state.puzzle.date) return;
  stats.played += 1;
  if (win) {
    stats.wins += 1;
    stats.streak = stats.lastDate === previousDate(state.puzzle.date) ? stats.streak + 1 : 1;
    stats.maxStreak = Math.max(stats.maxStreak, stats.streak);
    stats.dist[state.guesses.length - 1] += 1;
  } else {
    stats.streak = 0;
  }
  stats.lastDate = state.puzzle.date;
  localStorage.setItem("hammerdle:v1:stats", JSON.stringify(stats));
}

function renderStats() {
  const stats = loadStats();
  document.querySelector("#stat-played").textContent = String(stats.played);
  document.querySelector("#stat-win").textContent = stats.played ? String(Math.round((stats.wins / stats.played) * 100)) : "0";
  document.querySelector("#stat-streak").textContent = String(stats.streak);
  document.querySelector("#stat-max").textContent = String(stats.maxStreak);
  const max = Math.max(1, ...stats.dist);
  const dist = document.querySelector("#dist");
  dist.innerHTML = stats.dist.map((count, i) => {
    const width = Math.max(8, Math.round((count / max) * 100));
    const on = state.finished && state.guesses.length === i + 1 && state.guesses.at(-1)?.win;
    return `<div class="bar-row"><span>${i + 1}</span><div class="bar${on ? " on" : ""}" style="width:${width}%">${count}</div></div>`;
  }).join("");
}

function showResult(open) {
  const win = state.guesses.at(-1)?.win;
  document.querySelector("#result-title").textContent = win ? `Got it in ${state.guesses.length}` : "The hammer fell";
  const price = document.querySelector("#result-price");
  price.innerHTML = state.answer == null ? "" : `${escapeHtml(money(state.answer))}<br><span class="fine">${escapeHtml(dollars(state.answer))}</span>`;
  const detail = document.querySelector("#result-detail");
  if (state.puzzle.sourceUrl) {
    detail.innerHTML = `<a href="${escapeAttr(state.puzzle.sourceUrl)}">Source</a>`;
  } else {
    detail.textContent = "";
  }
  if (open) resultDialog.showModal();
}

function shareText() {
  const marks = state.guesses.map((guess) => {
    const color = guess.band === "win" ? "🟩" : guess.band === "close" ? "🟨" : "🟥";
    return color + arrow(guess);
  }).join("\n");
  const score = `${state.guesses.at(-1)?.win ? state.guesses.length : "X"}/${MAX}`;
  return `Hammerdle #${state.puzzle.number} ${score}\n\n${marks}`;
}

document.querySelector("#share").addEventListener("click", async () => {
  const text = shareText();
  const copied = document.querySelector("#copied");
  try {
    await navigator.clipboard.writeText(text);
    copied.textContent = "Copied.";
  } catch {
    copied.textContent = text;
  }
  copied.hidden = false;
});

document.querySelector("#units").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button || state.finished) return;
  state.unit = Number(button.dataset.unit);
  for (const item of document.querySelectorAll("#units button")) {
    const on = item === button;
    item.classList.toggle("on", on);
    item.setAttribute("aria-pressed", on ? "true" : "false");
  }
  amountInput.placeholder = state.unit === 1 ? "15000000" : state.unit === 1000 ? "15000" : "15";
  updatePreview();
  amountInput.focus();
});
amountInput.addEventListener("input", updatePreview);

document.querySelector("#help-btn").addEventListener("click", () => help.showModal());
document.querySelector("#stats-btn").addEventListener("click", () => {
  renderStats();
  statsDialog.showModal();
});
help.addEventListener("close", () => localStorage.setItem("hammerdle:v1:help-seen", "1"));

function tick() {
  const now = new Date();
  const next = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1);
  const left = next - now.getTime();
  const h = Math.floor(left / 3600000);
  const m = Math.floor((left % 3600000) / 60000);
  document.querySelector("#next").textContent = `Next puzzle in ${h}h ${String(m).padStart(2, "0")}m`;
}

setInterval(tick, 30000);
load().catch((error) => showStatus(error.message));
