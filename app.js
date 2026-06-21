const form = document.querySelector("#chat-form");
const input = document.querySelector("#prompt");
const messagesEl = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const statusEl = document.querySelector("#status");
const fullscreenToggle = document.querySelector("#fullscreen-toggle");
const cspxPriceCard = document.querySelector("#cspx-price-card");
const cspxPriceValue = document.querySelector("#cspx-price-value");
const cspxPriceMeta = document.querySelector("#cspx-price-meta");
const cspxRefresh = document.querySelector("#cspx-refresh");

const history = [];
let priceController;

function setStatus(text) {
  statusEl.textContent = text;
}

function setChatFullscreen(isFullscreen) {
  document.body.classList.toggle("chat-fullscreen", isFullscreen);
  fullscreenToggle.setAttribute("aria-pressed", String(isFullscreen));
  fullscreenToggle.textContent = isFullscreen ? "Close" : "Full screen";
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatAnswer(text) {
  return escapeHtml(text)
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${paragraph.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

function renderSources(sources = []) {
  if (!sources.length) return "";

  const links = sources
    .slice(0, 4)
    .map((source, index) => {
      const title = escapeHtml(source.title || source.url || `Source ${index + 1}`);
      const url = escapeHtml(source.url);
      return `<a class="source-link" href="${url}" target="_blank" rel="noreferrer"><span>${index + 1}. ${title}</span></a>`;
    })
    .join("");

  return `<div class="sources">${links}</div>`;
}

function createAvatar(role) {
  const avatar = document.createElement("div");
  avatar.className = "avatar";

  if (role === "assistant") {
    avatar.innerHTML = '<img src="/media/COLB_cool.webp" alt="" />';
  } else {
    avatar.innerHTML = '<img src="/media/COLB_sus.webp" alt="" />';
  }

  return avatar;
}

function addMessage(role, content, sources) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = `${formatAnswer(content)}${renderSources(sources)}`;

  article.append(createAvatar(role), bubble);
  messagesEl.append(article);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return article;
}

function addThinkingMessage() {
  const article = document.createElement("article");
  article.className = "message assistant thinking";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = `
    <div class="thinking-row" aria-label="Searching Colb docs">
      <span>Searching Colb docs</span>
      <span class="typing-dots" aria-hidden="true">
        <i></i><i></i><i></i>
      </span>
    </div>
  `;

  article.append(createAvatar("assistant"), bubble);
  messagesEl.append(article);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return article;
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  input.disabled = isLoading;
  document.querySelectorAll("[data-example]").forEach((button) => {
    button.disabled = isLoading;
  });
}

function autoresize() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
}

function formatUpdatedAt(value) {
  if (!value) return "BNB oracle";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "BNB oracle";
  return `BNB oracle - ${date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })}`;
}

async function loadCspxPrice() {
  if (priceController) priceController.abort();
  priceController = new AbortController();
  cspxPriceCard.dataset.state = "loading";
  cspxPriceValue.textContent = "Loading";
  cspxPriceMeta.textContent = "BNB oracle";

  try {
    const response = await fetch("/api/cspx-price", {
      signal: priceController.signal,
      headers: { accept: "application/json" }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Price unavailable");

    cspxPriceCard.dataset.state = "ready";
    cspxPriceValue.textContent = data.priceUsd || `$${data.price}`;
    cspxPriceMeta.textContent = formatUpdatedAt(data.updatedAt);
    cspxPriceCard.title = `${data.label} from ${data.source}`;
  } catch (error) {
    if (error.name === "AbortError") return;
    cspxPriceCard.dataset.state = "error";
    cspxPriceValue.textContent = "Unavailable";
    cspxPriceMeta.textContent = "Oracle temporarily unavailable";
  }
}

async function ask(question) {
  const cleanQuestion = question.trim();
  if (!cleanQuestion) return;

  addMessage("user", cleanQuestion);
  history.push({ role: "user", content: cleanQuestion });
  input.value = "";
  autoresize();
  setLoading(true);
  setStatus("thinking");

  const thinkingMessage = addThinkingMessage();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ messages: history.slice(-8) })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Request failed");
    }

    thinkingMessage.remove();
    addMessage("assistant", data.answer, data.sources);
    history.push({ role: "assistant", content: data.answer });
    setStatus("ready");
  } catch (error) {
    thinkingMessage.remove();
    addMessage("assistant", error.message || "Could not get an answer.");
    setStatus("error");
  } finally {
    setLoading(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(input.value);
});

input.addEventListener("input", autoresize);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => ask(button.dataset.example));
});

fullscreenToggle.addEventListener("click", () => {
  setChatFullscreen(!document.body.classList.contains("chat-fullscreen"));
});

cspxRefresh.addEventListener("click", loadCspxPrice);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.body.classList.contains("chat-fullscreen")) {
    setChatFullscreen(false);
  }
});

autoresize();
loadCspxPrice();
setInterval(loadCspxPrice, 60_000);
