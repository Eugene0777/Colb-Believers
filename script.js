/* ============================================================
   GLOBAL STATE
============================================================ */

let leaderboardBase = [];
let leaderboardData = [];
let allTweets = [];

let sortKey = "views";
let sortOrder = "desc";

let currentPage = 1;
const perPage = 12;

let timeFilter = "all";

/* ============================================================
   HELPERS
============================================================ */

function parseDateSafe(v) {
    if (!v) return null;
    const d = new Date(v);
    return isNaN(d.getTime()) ? null : d;
}

function daysDiff(a, b) {
    return (b - a) / (1000 * 60 * 60 * 24);
}

function cleanHandle(v) {
    return String(v || "")
        .replace(/^@/, "")
        .trim()
        .toLowerCase();
}

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

/* ============================================================
   NORMALIZE LEADERBOARD  (REAL FORMAT)
============================================================ */

function normalizeLeaderboard(raw) {
    if (!Array.isArray(raw)) return [];

    return raw.map(entry => {
        const username = entry[0];
        const s = entry[1] || {};

        return {
            username,
            pfp: s.profile_image_url
                ? s.profile_image_url.replace("_normal", "")
                : null,

            posts: +s.posts || 0,
            likes: +s.likes || 0,
            retweets: +s.retweets || 0,
            comments: +s.comments || 0,
            views: +s.views || 0
        };
    });
}

/* ============================================================
   LOAD DATA
============================================================ */

async function fetchLeaderboard() {
    try {
        const res = await fetch("leaderboard.json", { cache: "no-store" });
        const json = await res.json();
        leaderboardBase = normalizeLeaderboard(json);
        console.log("Leaderboard entries:", leaderboardBase.length);
    } catch (e) {
        console.error("Error loading leaderboard.json", e);
        leaderboardBase = [];
    }
}

async function fetchTweets() {
    try {
        const res = await fetch("all_tweets.json", { cache: "no-store" });
        const json = await res.json();

        // Универсальная нормализация структуры
        if (Array.isArray(json)) {
            allTweets = json;
        } else if (json && typeof json === "object") {
            if (Array.isArray(json.data)) {
                allTweets = json.data;
            } else if (Array.isArray(json.tweets)) {
                allTweets = json.tweets;
            } else {
                // на всякий случай ищем любой массив в значениях объекта
                const anyArray = Object.values(json).find(v => Array.isArray(v));
                allTweets = anyArray || [];
            }
        } else {
            allTweets = [];
        }

        console.log("Tweets loaded:", allTweets.length);
    } catch (e) {
        console.error("Error loading all_tweets.json", e);
        allTweets = [];
    }
}

/* ============================================================
   GET USER TWEETS (with media support)
============================================================ */

function getTweetsForUser(username, days = "all") {
    const h = cleanHandle(username);
    const now = new Date();

    return allTweets.filter(t => {
        const u =
            cleanHandle(t.user?.screen_name) ||
            cleanHandle(t.user?.username) ||
            cleanHandle(t.user?.name);

        if (u !== h) return false;

        const created = parseDateSafe(t.created_at || t.created);
        if (!created) return false;

        if (days !== "all" && daysDiff(created, now) > Number(days)) return false;

        return true;
    });
}

/* ============================================================
   MAIN RECOMPUTE
============================================================ */

function recomputeLeaderboard() {
    leaderboardData = leaderboardBase.map(row =>
        timeFilter === "all"
            ? row
            : {
                username: row.username,
                pfp: row.pfp,
                ...aggregateUserTweets(row.username, timeFilter)
            }
    );

    sortLeaderboard();
    renderTotals();
    renderFeed();
}

function aggregateUserTweets(username, days) {
    const target = cleanHandle(username);
    const now = new Date();
    const maxDays = days === "all" ? "all" : Number(days);

    let posts = 0, likes = 0, rts = 0, cm = 0, vw = 0;

    allTweets.forEach(t => {
        const u =
            cleanHandle(t.user?.screen_name) ||
            cleanHandle(t.user?.username) ||
            cleanHandle(t.user?.name);

        if (u !== target) return;

        const created = parseDateSafe(t.created_at || t.created);
        if (!created) return;

        if (maxDays !== "all" && daysDiff(created, now) > maxDays) return;

        posts++;
        likes += +t.favorite_count || 0;
        rts += +t.retweet_count || 0;
        cm += +t.reply_count || 0;
        vw += +t.views_count || 0;
    });

    return { posts, likes, retweets: rts, comments: cm, views: vw };
}

/* ============================================================
   SORT + FILTER
============================================================ */

function sortLeaderboard() {
    leaderboardData.sort((a, b) =>
        sortOrder === "asc"
            ? (a[sortKey] || 0) - (b[sortKey] || 0)
            : (b[sortKey] || 0) - (a[sortKey] || 0)
    );
}

function filteredLeaderboard() {
    const q = document.getElementById("search").value.trim().toLowerCase();
    return q
        ? leaderboardData.filter(u => u.username.toLowerCase().includes(q))
        : leaderboardData;
}

/* ============================================================
   TOTALS
============================================================ */

function renderTotals() {
    document.getElementById("total-posts").textContent =
        "Posts: " + leaderboardData.reduce((s, u) => s + (u.posts || 0), 0);

    document.getElementById("total-users").textContent =
        "Users: " + leaderboardData.length;

    document.getElementById("total-views").textContent =
        "Views: " + leaderboardData.reduce((s, u) => s + (u.views || 0), 0);
}

/* ============================================================
   RENDER FEED
============================================================ */

function renderFeed() {
    const container = document.getElementById("feed-container");
    container.innerHTML = "";

    const filtered = filteredLeaderboard();
    const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));

    if (currentPage > totalPages) currentPage = totalPages;

    const start = (currentPage - 1) * perPage;
    const slice = filtered.slice(start, start + perPage);

    slice.forEach(row => {
        const username = row.username;
        const handle = cleanHandle(username);
        const pfp = row.pfp;
        const letter = username[0]?.toUpperCase() || "?";

        const card = document.createElement("article");
        card.className = "user-card";

        card.innerHTML = `
            <div class="user-avatar">
                ${pfp ? `<img src="${pfp}">` : letter}
            </div>

            <div class="user-name">${escapeHtml(username)}</div>
            <div class="user-handle">@${escapeHtml(handle)}</div>

            <div class="user-stats">
                <div class="user-stat-pill">${row.posts} posts</div>
                <div class="user-stat-pill">${row.likes} likes</div>
                <div class="user-stat-pill">${row.retweets} rts</div>
                <div class="user-stat-pill">${row.comments} cmts</div>
                <div class="user-stat-pill">${row.views} views</div>
            </div>
        `;

        card.addEventListener("click", () => openTweetsModal(username));
        container.appendChild(card);
    });

    document.getElementById("page-info").textContent =
        `Page ${currentPage} / ${totalPages}`;
}

/* ============================================================
   MODAL WITH TWEETS + MEDIA
============================================================ */

function openTweetsModal(username) {
    const modal = document.getElementById("tweets-modal");
    const body = document.getElementById("modal-body");
    const title = document.getElementById("modal-title");

    modal.classList.remove("hidden");
    title.textContent = `Tweets by ${username}`;
    body.innerHTML = "<p style='color:#aaa'>Loading…</p>";

    const tweets = getTweetsForUser(username, timeFilter);
    console.log("User tweets for", username, "=", tweets.length);

    if (!tweets.length) {
        body.innerHTML = "<p style='color:#777'>No tweets found.</p>";
        return;
    }

    body.innerHTML = "";
    tweets.forEach(t => body.appendChild(renderTweetCard(t)));
}

function renderTweetCard(t) {
    const created = parseDateSafe(t.created_at || t.created);
    const dateStr = created
        ? created.toLocaleDateString(undefined, {
              year: "numeric",
              month: "short",
              day: "numeric"
          })
        : "";

    let mediaHtml = "";

    if (Array.isArray(t.media) && t.media.length > 0) {
        mediaHtml = `
        <div class="tweet-media ${getMediaLayoutClass(t.media.length)}">
            ${t.media.map(m => renderMediaItem(m)).join("")}
        </div>`;
    }

    const card = document.createElement("article");
    card.className = "profile-tweet-card";

    card.innerHTML = `
        <p class="tweet-text">${escapeHtml(t.text || "")}</p>
        ${mediaHtml}
        <div class="profile-tweet-meta">
            <span>${dateStr}</span>
            <span>
                ❤️ ${t.favorite_count || 0}
                · 💬 ${t.reply_count || 0}
                · 🔁 ${t.retweet_count || 0}
                · 👁 ${t.views_count || 0}
            </span>
        </div>
    `;

    return card;
}

/* Layout classes for media grid */
function getMediaLayoutClass(count) {
    if (count === 1) return "one";
    if (count === 2) return "two";
    if (count === 3) return "three";
    return "four";
}

/* Render photo / GIF / video */
function renderMediaItem(m) {
    if (!m) return "";

    if (m.type === "photo")
        return `<img class="tweet-img" src="${m.url}" loading="lazy">`;

    if (m.type === "video")
        return `
            <video class="tweet-img" controls>
                <source src="${m.video_url}">
            </video>
        `;

    if (m.type === "animated_gif")
        return `
            <video class="tweet-img" autoplay loop muted>
                <source src="${m.video_url}">
            </video>
        `;

    return "";
}

/* ============================================================
   CLOSE MODAL
============================================================ */

document.getElementById("modal-close").addEventListener("click", () => {
    document.getElementById("tweets-modal").classList.add("hidden");
});

document.getElementById("tweets-modal").addEventListener("click", e => {
    if (e.target.id === "tweets-modal") {
        e.target.classList.add("hidden");
    }
});

/* ============================================================
   CONTROLS
============================================================ */

function setupControls() {
    document.getElementById("search").addEventListener("input", () => {
        currentPage = 1;
        renderFeed();
    });

    document.getElementById("time-select").addEventListener("change", e => {
        timeFilter = e.target.value;
        currentPage = 1;
        recomputeLeaderboard();
    });

    document.getElementById("sort-select").addEventListener("change", e => {
        sortKey = e.target.value;
        sortLeaderboard();
        renderFeed();
    });

    document.getElementById("sort-order-btn").addEventListener("click", e => {
        sortOrder = sortOrder === "asc" ? "desc" : "asc";
        e.target.textContent =
            sortOrder === "asc" ? "▲ Asc" : "▼ Desc";
        sortLeaderboard();
        renderFeed();
    });

    document.getElementById("prev-page").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderFeed();
        }
    });

    document.getElementById("next-page").addEventListener("click", () => {
        const total = Math.ceil(filteredLeaderboard().length / perPage);
        if (currentPage < total) {
            currentPage++;
            renderFeed();
        }
    });
}

/* ============================================================
   INIT
============================================================ */

document.addEventListener("DOMContentLoaded", async () => {
    setupControls();

    await fetchTweets();
    await fetchLeaderboard();

    recomputeLeaderboard();
});

/* ============================================================
   Smooth Bees — Constant Speed, No Disappear, Natural Flight
============================================================ */

const BEE_COUNT = 7;
const SPEED = 0.6; // скорость — медленная, постоянная
const SAFE = 60;   // отступ от краёв

let beesArr = [];

function spawnFlyingBees() {
    const container = document.getElementById("flying-bees-container");

    for (let i = 0; i < BEE_COUNT; i++) {

        const bee = document.createElement("img");
        bee.src = "media/bee.png";
        bee.className = "flying-bee";

        // Начальная позиция
        let x = Math.random() * (window.innerWidth - SAFE * 2) + SAFE;
        let y = Math.random() * (window.innerHeight - SAFE * 2) + SAFE;

        // Вектор направления (мягкий)
        let angle = Math.random() * Math.PI * 2;
        let dx = Math.cos(angle) * SPEED;
        let dy = Math.sin(angle) * SPEED;

        beesArr.push({ el: bee, x, y, dx, dy, angle });

        bee.style.left = x + "px";
        bee.style.top = y + "px";

        container.appendChild(bee);
    }

    requestAnimationFrame(updateBees);
}

function updateBees() {

    beesArr.forEach(bee => {
        const el = bee.el;

        // движение
        bee.x += bee.dx;
        bee.y += bee.dy;

        let bounced = false;

        // отражение от краёв экрана — улучшенное
        if (bee.x < SAFE) {
            bee.x = SAFE + 2; // толкаем от стены
            bee.dx = Math.abs(bee.dx); // двигаем вправо
            bounced = true;
        }
        if (bee.x > window.innerWidth - SAFE) {
            bee.x = window.innerWidth - SAFE - 2; 
            bee.dx = -Math.abs(bee.dx); // двигаем влево
            bounced = true;
        }

        if (bee.y < SAFE) {
            bee.y = SAFE + 2;
            bee.dy = Math.abs(bee.dy); // вниз
            bounced = true;
        }
        if (bee.y > window.innerHeight - SAFE) {
            bee.y = window.innerHeight - SAFE - 2;
            bee.dy = -Math.abs(bee.dy); // вверх
            bounced = true;
        }

        // если был "удар" — корректируем угол и не делаем случайный поворот
        if (bounced) {
            bee.angle = Math.atan2(bee.dy, bee.dx);
        } 
        else {
            // редкий мягкий поворот
            if (Math.random() < 0.01) {
                const turn = (Math.random() - 0.5) * 0.25;
                bee.angle += turn;
                bee.dx = Math.cos(bee.angle) * SPEED;
                bee.dy = Math.sin(bee.angle) * SPEED;
            }
        }

        // обновить позицию
        el.style.left = bee.x + "px";
        el.style.top = bee.y + "px";

        // повернуть пчелу по направлению движения
        const angleDeg = Math.atan2(bee.dy, bee.dx) * 180 / Math.PI;
        el.style.transform = `rotate(${angleDeg + 90}deg)`;
    });

    requestAnimationFrame(updateBees);
}


document.addEventListener("DOMContentLoaded", spawnFlyingBees);
