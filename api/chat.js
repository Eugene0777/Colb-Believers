import { existsSync, readFileSync } from "node:fs";

const FALLBACK_ANSWER = "The Colb documentation does not contain information about this question.";
const DEFAULT_MODEL = "openai/gpt-4.1-mini";
const MAX_CONTEXT_CHARS = 18000;
const MIN_RELEVANCE_SCORE = 4;
const DOCS_INDEX_URL = new URL("../data/docs.json", import.meta.url);

const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "can",
  "do",
  "does",
  "for",
  "from",
  "how",
  "i",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "this",
  "to",
  "what",
  "when",
  "where",
  "which",
  "who",
  "why",
  "with"
]);

const SYNONYM_HINTS = new Map([
  ["invest", "invest investment"],
  ["pay", "pay payment"],
  ["wallet", "wallet"],
  ["docs", "documentation docs"],
  ["get", "getting started onboarding"],
  ["start", "getting started onboarding"],
  ["started", "getting started onboarding"],
  ["onboard", "onboarding getting started"],
  ["contract", "smart contract contracts"],
  ["token", "token"],
  ["withdraw", "withdraw withdrawal redemption"],
  ["redeem", "redeem redemption withdrawal"],
  ["deposit", "deposit"],
  ["fee", "fee fees"],
  ["risk", "risk"],
  ["account", "account"],
  ["profile", "profile"],
  ["usc", "usc stablecoin payment"]
]);

const PINNED_PAGE_HINTS = [
  {
    patterns: ["colb liquids", "liquids"],
    urlPart: "/investment-core-tech/colb-liquids"
  },
  {
    patterns: ["cbal", "colb usd balanced", "usd balanced strategy"],
    urlPart: "/products/tokenized-managed-strategies/cbal"
  }
];

function loadDocsIndex() {
  try {
    return JSON.parse(readFileSync(DOCS_INDEX_URL, "utf8"));
  } catch {
    return { pages: [], chunks: [] };
  }
}

const docsIndex = loadDocsIndex();

function loadEnv() {
  if (process.env.OPENROUTER_API_KEY) return;

  try {
    const envPath = new URL("../.env", import.meta.url);
    if (!existsSync(envPath)) return;

    const content = readFileSync(envPath, "utf8");
    for (const line of content.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) continue;
      const [key, ...rest] = trimmed.split("=");
      const value = rest.join("=").trim().replace(/^['"]|['"]$/g, "");
      if (!process.env[key]) process.env[key] = value;
    }
  } catch {
    // Vercel provides env vars directly; local .env loading is best-effort.
  }
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk) => {
      raw += chunk;
      if (raw.length > 64_000) {
        reject(new Error("Payload is too large"));
        req.destroy();
      }
    });
    req.on("end", () => {
      try {
        resolve(raw ? JSON.parse(raw) : {});
      } catch {
        reject(new Error("Invalid JSON"));
      }
    });
    req.on("error", reject);
  });
}

function send(res, statusCode, payload) {
  res.statusCode = statusCode;
  res.setHeader("content-type", "application/json; charset=utf-8");
  res.end(JSON.stringify(payload));
}

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\p{L}\p{N}\s-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(value) {
  const normalized = normalize(value);
  const tokens = normalized
    .split(" ")
    .map((token) => token.trim())
    .filter((token) => token.length > 1 && !STOPWORDS.has(token));

  const extra = [];
  for (const token of tokens) {
    for (const [prefix, expansion] of SYNONYM_HINTS.entries()) {
      if (token.startsWith(prefix)) extra.push(...expansion.split(" "));
    }
  }

  return [...new Set([...tokens, ...extra])];
}

function hasNonAscii(value) {
  return /[^\x00-\x7F]/.test(value);
}

function isUnsupportedAdviceQuestion(value) {
  const text = normalize(value);
  const futureTime =
    text.includes("next year") ||
    text.includes("tomorrow") ||
    text.includes("next month") ||
    text.includes("future") ||
    /\bin\s+20\d{2}\b/.test(text);
  const priceTopic = text.includes("price") || text.includes("value") || text.includes("worth");

  if (futureTime && priceTopic) return true;

  const patterns = [
    "should i buy",
    "which token should i buy",
    "what token should i buy",
    "make the most profit",
    "most profitable",
    "price next year",
    "future price",
    "price prediction",
    "predict the price",
    "forecast",
    "investment advice",
    "financial advice"
  ];

  return patterns.some((pattern) => text.includes(pattern));
}

function buildSearchText(messages) {
  return messages
    .filter((message) => message.role === "user")
    .slice(-4)
    .map((message) => message.content)
    .join("\n");
}

function scoreChunk(chunk, tokens, phrase) {
  const title = normalize(chunk.title);
  const heading = normalize(chunk.heading);
  const path = normalize(`${chunk.url || ""} ${chunk.id || ""}`);
  const text = normalize(chunk.text);
  let score = 0;

  for (const token of tokens) {
    if (title.includes(token)) score += 8;
    if (heading.includes(token)) score += 5;
    if (path.includes(token)) score += 6;
    if (text.includes(token)) score += 1;
  }

  if (phrase.length > 8 && path.includes(phrase)) score += 12;
  if (phrase.length > 8 && text.includes(phrase)) score += 12;
  return score;
}

function pinnedChunks(query) {
  const text = normalize(query);
  const pinned = [];

  for (const hint of PINNED_PAGE_HINTS) {
    if (!hint.patterns.some((pattern) => text.includes(pattern))) continue;
    pinned.push(...docsIndex.chunks.filter((chunk) => chunk.url?.includes(hint.urlPart)));
  }

  return pinned;
}

function retrieve(query, limit = 8) {
  const tokens = tokenize(query);
  if (!tokens.length) return [];
  const phrase = normalize(query);
  const pinned = pinnedChunks(query);
  const pinnedIds = new Set(pinned.map((chunk) => chunk.id));
  const scoredLimit = Math.max(limit - pinned.length, 0);

  const scored = docsIndex.chunks
    .filter((chunk) => !pinnedIds.has(chunk.id))
    .map((chunk) => ({ chunk, score: scoreChunk(chunk, tokens, phrase) }))
    .filter((item) => item.score >= MIN_RELEVANCE_SCORE)
    .sort((a, b) => b.score - a.score)
    .slice(0, scoredLimit)
    .map((item) => item.chunk);

  return [...pinned, ...scored].slice(0, limit);
}

function buildContext(chunks) {
  let used = 0;
  const blocks = [];

  for (const [index, chunk] of chunks.entries()) {
    const header = `[${index + 1}] ${chunk.title}${chunk.heading ? ` / ${chunk.heading}` : ""}\nURL: ${chunk.url}`;
    const body = chunk.text.slice(0, 2600);
    const block = `${header}\n${body}`;
    if (used + block.length > MAX_CONTEXT_CHARS) break;
    blocks.push(block);
    used += block.length;
  }

  return blocks.join("\n\n---\n\n");
}

function dedupeSources(chunks) {
  const seen = new Set();
  const sources = [];

  for (const chunk of chunks) {
    if (seen.has(chunk.url)) continue;
    seen.add(chunk.url);
    sources.push({ title: chunk.title, url: chunk.url });
  }

  return sources.slice(0, 4);
}

async function callOpenRouter(messages, { maxTokens = 750, temperature = 0 } = {}) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is not set. Add it to .env locally and to Vercel Environment Variables.");
  }

  const model = process.env.OPENROUTER_MODEL || DEFAULT_MODEL;
  const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      authorization: `Bearer ${apiKey}`,
      "content-type": "application/json",
      "http-referer": process.env.OPENROUTER_HTTP_REFERER || "http://localhost:3000",
      "x-title": process.env.OPENROUTER_APP_TITLE || "Colb Docs AI"
    },
    body: JSON.stringify({
      model,
      messages,
      temperature,
      max_tokens: maxTokens
    })
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.error?.message || `OpenRouter request failed with ${response.status}`;
    throw new Error(message);
  }

  return payload.choices?.[0]?.message?.content?.trim() || "";
}

async function rewriteQuery(searchText) {
  const answer = await callOpenRouter(
    [
      {
        role: "system",
        content:
          "Translate the user's question into concise English search keywords for documentation retrieval. Do not answer the question. Return only keywords."
      },
      { role: "user", content: searchText }
    ],
    { maxTokens: 80, temperature: 0 }
  );

  return answer.replace(/[^\p{L}\p{N}\s-]/gu, " ").replace(/\s+/g, " ").trim();
}

function buildAnswerMessages(messages, context) {
  const compactHistory = messages.slice(-6).map((message) => ({
    role: message.role === "assistant" ? "assistant" : "user",
    content: String(message.content || "").slice(0, 1600)
  }));

  return [
    {
      role: "system",
      content: [
        "You are the Colb documentation assistant.",
        "HARD RULES:",
        "- Answer only from the CONTEXT below.",
        `- If the CONTEXT does not contain enough information, answer exactly: ${FALLBACK_ANSWER}`,
        "- Do not use outside knowledge, assumptions, or guesses.",
        "- Always answer in English, even if the user writes in another language.",
        "- Be concise and practical. Keep the whole answer under 180 words unless the user explicitly asks for a full procedure.",
        "- Use at most 10 bullets.",
        "- If the context contains a long table, long address list, or many smart contracts, summarize categories/networks and point to the source instead of dumping every row.",
        "- Never include more than 3 contract addresses unless the latest user message explicitly asks for addresses.",
        "- Only provide a full address list when the latest user message explicitly asks for all addresses or the full list.",
        "- Do not add inline numeric citations; the app displays source links separately.",
        "",
        "CONTEXT:",
        context
      ].join("\n")
    },
    ...compactHistory
  ];
}

export default async function handler(req, res) {
  loadEnv();

  if (req.method !== "POST") {
    send(res, 405, { error: "Method not allowed" });
    return;
  }

  try {
    const body = await readJsonBody(req);
    const messages = Array.isArray(body.messages) ? body.messages : [];
    const latestUserMessage = [...messages].reverse().find((message) => message.role === "user");

    if (!latestUserMessage?.content?.trim()) {
      send(res, 400, { error: "Question is required" });
      return;
    }

    if (isUnsupportedAdviceQuestion(latestUserMessage.content)) {
      send(res, 200, { answer: FALLBACK_ANSWER, sources: [] });
      return;
    }

    if (!docsIndex.chunks?.length) {
      send(res, 200, {
        answer: "The documentation index is empty. Run `npm run ingest`, then deploy the project again.",
        sources: []
      });
      return;
    }

    const searchText = buildSearchText(messages);
    let chunks = retrieve(searchText);

    if (chunks.length < 2 && hasNonAscii(searchText) && process.env.OPENROUTER_API_KEY) {
      const rewritten = await rewriteQuery(searchText);
      chunks = retrieve(`${searchText}\n${rewritten}`);
    }

    if (!chunks.length) {
      send(res, 200, { answer: FALLBACK_ANSWER, sources: [] });
      return;
    }

    const context = buildContext(chunks);
    const answer = await callOpenRouter(buildAnswerMessages(messages, context));
    const cleanAnswer = answer || FALLBACK_ANSWER;
    const noInfo = cleanAnswer.toLowerCase().includes("does not contain information");

    send(res, 200, {
      answer: cleanAnswer,
      sources: noInfo ? [] : dedupeSources(chunks),
      index: {
        pages: docsIndex.pages?.length || 0,
        chunks: docsIndex.chunks?.length || 0,
        generatedAt: docsIndex.generatedAt
      }
    });
  } catch (error) {
    send(res, 500, { error: error.message || "Unexpected server error" });
  }
}

export const config = {
  api: {
    bodyParser: false
  }
};
