import json
import time
import logging
import random
import requests
from urllib.parse import urlparse
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

API_KEY = os.getenv("SOCIALDATA_API_KEY")
COMMUNITY_ID = "1965795131186954572"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}

ALL_TWEETS_FILE = "all_tweets.json"
LEADERBOARD_FILE = "leaderboard.json"

LINK_TWEETS = [
    "https://twitter.com/jacks12300711/status/1990541572342231158",
    "https://twitter.com/jacks12300711/status/1990711670499385494",
    "https://twitter.com/jacks12300711/status/1991123841674846261",
    "https://twitter.com/jacks12300711/status/1991600494406684714",
    "https://twitter.com/jacks12300711/status/1992326454005428606",
    "https://twitter.com/jacks12300711/status/1993051269750239722",
    "https://twitter.com/jacks12300711/status/1993792499434037318",
    "https://twitter.com/jacks12300711/status/1995083592066793944",
    "https://twitter.com/jacks12300711/status/1996480946216874462",
    "https://twitter.com/jacks12300711/status/1997238765493145988",
]



def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_tweet_id(tweet_url: str) -> str:
    parsed = urlparse(tweet_url)
    parts = parsed.path.strip("/").split("/")
    if "status" in parts:
        idx = parts.index("status")
        return parts[idx + 1].split("?")[0]
    raise ValueError(f"Не могу извлечь ID из URL: {tweet_url}")




def safe_request(url, params=None, retries=8, timeout=30):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()

        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            logging.warning(f"⛔ NETWORK ISSUE {attempt}/{retries} — retrying...")

        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠ Ошибка сети ({attempt}/{retries}): {e}")

        sleep_time = min(12, 2**attempt + random.uniform(0, 1))
        logging.info(f"⏳ Жду {sleep_time:.1f} сек и повторяю...")
        time.sleep(sleep_time)

    raise RuntimeError(f"❌ API не отвечает после {retries} попыток: {url}")




def extract_best_video(media):
    if media.get("type") not in ("video", "animated_gif"):
        return None

    variants = media.get("video_info", {}).get("variants", [])
    if not variants:
        return None

    video_variants = [
        v for v in variants
        if v.get("content_type", "").startswith("video")
    ]

    if not video_variants:
        return None

    best = max(video_variants, key=lambda v: v.get("bitrate", 0))
    return best.get("url")


def extract_media(tweet):
    media = []

    if "extended_entities" in tweet and "media" in tweet["extended_entities"]:
        media = tweet["extended_entities"]["media"]
    elif "entities" in tweet and "media" in tweet["entities"]:
        media = tweet["entities"]["media"]
    elif "media" in tweet:
        media = tweet["media"]

    unique = []
    seen = set()

    for m in media:
        url = m.get("media_url_https") or m.get("media_url")
        if not url:
            continue

        if url in seen:
            continue  # удаление дубля

        seen.add(url)

        unique.append({
            "type": m.get("type"),
            "url": url,
            "thumb": m.get("url"),
            "video_url": extract_best_video(m),
        })

    return unique




def normalize_tweet(tweet: dict) -> dict:
    user = tweet.get("user", {}) or {}
    text = tweet.get("full_text") or tweet.get("text")

    return {
        "created_at": tweet.get("tweet_created_at") or tweet.get("created_at"),
        "id_str": tweet.get("id_str"),
        "text": text,
        "favorite_count": tweet.get("favorite_count", 0),
        "retweet_count": tweet.get("retweet_count", 0),
        "reply_count": tweet.get("reply_count", 0),
        "views_count": tweet.get("views_count", 0),
        "quote_count": tweet.get("quote_count", 0),
        "media": extract_media(tweet),
        "user": {
            "screen_name": user.get("screen_name"),
            "name": user.get("name"),
            "profile_image_url":
                user.get("profile_image_url_https") or user.get("profile_image_url"),
        }
    }




def fetch_community_page(cursor=None, limit=100):
    params = {"type": "Latest", "limit": limit}
    if cursor:
        params["cursor"] = cursor

    url = f"https://api.socialdata.tools/twitter/community/{COMMUNITY_ID}/tweets"
    return safe_request(url, params=params)


def collect_all_community_tweets():
    logging.info("\n=========== СБОР КОМЬЮНИТИ — УМНЫЙ РЕЖИМ ===========")

    all_tweets = []
    seen = set()
    cursor = None
    page = 0

    while True:
        page += 1
        logging.info(f"\n---- СТРАНИЦА #{page} ---- cursor={cursor}")

        data = fetch_community_page(cursor)
        tweets = data.get("tweets", [])
        next_cursor = data.get("next_cursor")

        logging.info(f"Получено твитов: {len(tweets)}, next_cursor={next_cursor}")

        new_count = 0
        for t in tweets:
            tid = t.get("id_str")
            if tid and tid not in seen:
                seen.add(tid)
                all_tweets.append(t)
                new_count += 1

        logging.info(f"➕ новых: {new_count} | всего: {len(all_tweets)}")

        # ================= АНТИ-ЛОЖНЫЙ КОНЕЦ =================
        if len(tweets) == 0:
            logging.warning("⚠ Пустая страница — проверяем, не ложный ли это конец...")

            retry_success = False

            # 1) 12 повторов
            for attempt in range(1, 13):
                delay = attempt
                logging.info(f"🔄 Повтор #{attempt}, жду {delay} сек...")
                time.sleep(delay)

                retry = fetch_community_page(cursor)
                retry_tweets = retry.get("tweets", [])
                retry_cursor = retry.get("next_cursor")

                if retry_tweets:
                    logging.info("✔ ЛОЖНЫЙ КОНЕЦ: данные появились!")

                    added = 0
                    for t in retry_tweets:
                        tid = t.get("id_str")
                        if tid and tid not in seen:
                            seen.add(tid)
                            all_tweets.append(t)
                            added += 1

                    logging.info(f"➕ добавлено после повтора: {added}")
                    tweets = retry_tweets
                    next_cursor = retry_cursor
                    retry_success = True
                    break

            # 2) если всё пусто — пауза 3 минуты
            if not retry_success:
                logging.warning("⏸ Пауза 3 минуты...")
                time.sleep(180)

                retry2 = fetch_community_page(cursor)
                retry2_tweets = retry2.get("tweets", [])
                retry2_cursor = retry2.get("next_cursor")

                if retry2_tweets:
                    logging.info("✔ После паузы данные появились!")

                    added = 0
                    for t in retry2_tweets:
                        tid = t.get("id_str")
                        if tid and tid not in seen:
                            seen.add(tid)
                            all_tweets.append(t)
                            added += 1

                    tweets = retry2_tweets
                    next_cursor = retry2_cursor
                else:
                    logging.info("🏁 Истинный конец — данных нет даже после паузы.")
                    break

        if next_cursor is None:
            logging.info("🏁 next_cursor=None — конец истории.")
            break

        cursor = next_cursor
        time.sleep(0.6)

    logging.info(f"\n=== ГОТОВО: собрано уникальных твитов: {len(all_tweets)} ===")
    return all_tweets




def fetch_single_tweet(tweet_id: str):
    url = f"https://api.socialdata.tools/twitter/tweets/{tweet_id}"
    return safe_request(url)


def collect_links_tweets():
    logging.info("\n=========== СБОР ТВИТОВ ПО ССЫЛКАМ ===========")
    results = []

    for url in LINK_TWEETS:
        logging.info(f"URL: {url}")

        try:
            tid = extract_tweet_id(url)
            raw = fetch_single_tweet(tid)
            results.append(normalize_tweet(raw))
            logging.info(f"✓ Успех: {tid}")

        except Exception as e:
            logging.error(f"✗ Ошибка для {url}: {e}")

    return results


# ============================================================
# MERGE
# ============================================================

def merge_tweets(community_raw, link_norm):
    logging.info("\n=========== ОБЪЕДИНЕНИЕ РЕЗУЛЬТАТОВ ===========")

    final = []
    seen = set()

    for tw in community_raw:
        n = normalize_tweet(tw)
        tid = n.get("id_str")
        if tid and tid not in seen:
            seen.add(tid)
            final.append(n)

    for tw in link_norm:
        tid = tw.get("id_str")
        if tid and tid not in seen:
            seen.add(tid)
            final.append(tw)

    logging.info(f"🔥 Итого после объединения: {len(final)} твитов")
    return final


# ============================================================
# LEADERBOARD
# ============================================================

def build_leaderboard(tweets):
    board = {}

    for t in tweets:
        user = (t.get("user") or {}).get("screen_name") or "unknown"
        pfp = (t.get("user") or {}).get("profile_image_url")

        stats = board.setdefault(user, {
            "profile_image_url": pfp,
            "posts": 0,
            "likes": 0,
            "retweets": 0,
            "comments": 0,
            "quotes": 0,
            "views": 0,
        })

        stats["posts"] += 1
        stats["likes"] += t.get("favorite_count", 0)
        stats["retweets"] += t.get("retweet_count", 0)
        stats["comments"] += t.get("reply_count", 0)
        stats["quotes"] += t.get("quote_count", 0)
        stats["views"] += t.get("views_count", 0)

    return [[user, stats] for user, stats in board.items()]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    community_raw = collect_all_community_tweets()
    link_tweets = collect_links_tweets()

    all_tweets = merge_tweets(community_raw, link_tweets)
    save_json(ALL_TWEETS_FILE, all_tweets)
    logging.info(f"💾 {ALL_TWEETS_FILE} сохранён ({len(all_tweets)} твитов)")

    leaderboard = build_leaderboard(all_tweets)
    save_json(LEADERBOARD_FILE, leaderboard)
    logging.info(f"💾 {LEADERBOARD_FILE} сохранён")



