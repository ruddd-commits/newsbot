"""
╔══════════════════════════════════════════════════════════════╗
║         MASTER NEWS BOT — SAHAM • FOREX • CRYPTO • MAKRO     ║
║         Telegram Channel Auto-Poster  |  GitHub Actions Ed.  ║
╚══════════════════════════════════════════════════════════════╝
"""

import feedparser
import requests
import hashlib
import json
import os
import re
import sys
import logging
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# ─────────────────────────────────────────────
#  KONFIGURASI  (ambil dari environment / GitHub Secrets)
# ─────────────────────────────────────────────
BOT_TOKEN          = os.environ["8722488665:AAH_K6anoithS9v3Wb9KDraoC5i7UMtcbU8"]
CHANNEL_ID         = os.environ["@scrabingnews"]

SEEN_FILE          = "seen_articles.json"
MAX_PER_SOURCE     = 20
REQUEST_TIMEOUT    = 10
DELAY_BETWEEN_SEND = 2
MAX_AGE_HOURS      = 4          # hanya berita dalam N jam terakhir

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  MASTER SOURCE LIST
# ─────────────────────────────────────────────
SOURCES = {
    "🌍 INTERNASIONAL": [
        {"name": "Reuters",        "url": "https://feeds.reuters.com/reuters/topNews"},
        {"name": "Reuters Bisnis", "url": "https://feeds.reuters.com/reuters/businessNews"},
        {"name": "CNBC",           "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
        {"name": "CNBC World",     "url": "https://www.cnbc.com/id/100727362/device/rss/rss.html"},
        {"name": "MarketWatch",    "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
        {"name": "Nikkei Asia",    "url": "https://asia.nikkei.com/rss/feed/nar"},
        {"name": "FT Markets",     "url": "https://www.ft.com/markets?format=rss"},
    ],
    "📈 SAHAM & EQUITIES": [
        {"name": "Seeking Alpha",  "url": "https://seekingalpha.com/feed.xml"},
        {"name": "Benzinga",       "url": "https://www.benzinga.com/feed"},
        {"name": "Investor's Biz", "url": "https://www.investors.com/feed/"},
        {"name": "Motley Fool",    "url": "https://www.fool.com/a/feeds/foolwatch?format=rss&id=foolwatch&apikey=foolwatch"},
        {"name": "Yahoo Finance",  "url": "https://finance.yahoo.com/rss/topfinstories"},
    ],
    "💱 FOREX & RATES": [
        {"name": "ForexLive",         "url": "https://www.forexlive.com/feed/news"},
        {"name": "FXStreet",          "url": "https://www.fxstreet.com/rss/news"},
        {"name": "DailyFX",           "url": "https://www.dailyfx.com/feeds/all"},
        {"name": "Investing.com",     "url": "https://www.investing.com/rss/news_301.rss"},
        {"name": "Trading Economics", "url": "https://tradingeconomics.com/rss/news.aspx"},
    ],
    "🪙 CRYPTO & BLOCKCHAIN": [
        {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "The Block",     "url": "https://www.theblock.co/rss.xml"},
        {"name": "Decrypt",       "url": "https://decrypt.co/feed"},
        {"name": "CryptoSlate",   "url": "https://cryptoslate.com/feed/"},
    ],
    "🌐 MAKRO & EKONOMI": [
        {"name": "IMF",             "url": "https://www.imf.org/en/News/rss?language=ENG"},
        {"name": "World Bank",      "url": "https://blogs.worldbank.org/rss.xml"},
        {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
        {"name": "ECB",             "url": "https://www.ecb.europa.eu/rss/press.html"},
        {"name": "Bank of England", "url": "https://www.bankofengland.co.uk/rss/news"},
    ],
    "🌍 GEOPOLITIK & ENERGI": [
        {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
        {"name": "AP News",    "url": "https://rsshub.app/apnews/topics/apf-topnews"},
        {"name": "Politico",   "url": "https://rss.politico.com/politics-news.xml"},
    ],
    "🇮🇩 INDONESIA": [
        {"name": "CNBC Indonesia", "url": "https://www.cnbcindonesia.com/rss"},
        {"name": "Bisnis.com",     "url": "https://rss.bisnis.com/topnews.rss"},
        {"name": "Kontan",         "url": "https://rss.kontan.co.id/kontan/investasi.rss"},
        {"name": "Investor.id",    "url": "https://investor.id/feed"},
    ],
}

TOTAL_SOURCES = sum(len(v) for v in SOURCES.values())


# ─────────────────────────────────────────────
#  KEYWORD FILTER
# ─────────────────────────────────────────────
KEYWORDS = [
    "market","stock","shares","index","equity","trading","rally","crash",
    "earnings","revenue","profit","loss","forecast","outlook","guidance",
    "dollar","euro","yen","pound","rate","fed","fomc","interest",
    "inflation","cpi","ppi","gdp","nonfarm","payroll","unemployment",
    "treasury","yield","bond","bitcoin","btc","ethereum","eth","crypto",
    "blockchain","token","defi","nft","etf","altcoin","halving","whale",
    "recession","imf","world bank","central bank","monetary","fiscal",
    "tariff","trade war","sanction","opec","oil","gold","commodity",
    "war","conflict","geopolit","china","russia","ukraine","taiwan",
    "nato","election","president","minister","policy","deal",
    "indonesia","rupiah","idr","ihsg","bi rate","ojk","bps","saham",
    "bursa","idx","obligasi","sbn","sri mulyani","prabowo","apbn",
]


def is_relevant(text: str) -> bool:
    return any(kw in text.lower() for kw in KEYWORDS)


# ─────────────────────────────────────────────
#  FILTER WAKTU
# ─────────────────────────────────────────────
def parse_published(entry) -> datetime | None:
    for field in ("published", "updated", "created"):
        raw = getattr(entry, field, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    for field in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def is_recent(entry) -> bool:
    dt = parse_published(entry)
    if dt is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    return dt >= cutoff


# ─────────────────────────────────────────────
#  SEEN CACHE  (anti-duplikat URL)
# ─────────────────────────────────────────────
def load_seen() -> set:
    try:
        if os.path.exists(SEEN_FILE):
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
    except Exception:
        pass
    return set()


def save_seen(seen: set):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(seen)[-5000:], f)
    except Exception as e:
        log.error(f"Gagal simpan cache: {e}")


def art_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


# ─────────────────────────────────────────────
#  ANTI-DUPLIKAT JUDUL
# ─────────────────────────────────────────────
def normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    stopwords = {
        "the","a","an","is","are","in","on","at","to","of","for",
        "and","or","with","by","from","as","that","this","it","be",
        "has","have","was","were","will","can","its","their","says","said","new",
    }
    words = [w for w in t.split() if w not in stopwords]
    return " ".join(words[:8])


def title_hash(title: str) -> str:
    return hashlib.md5(normalize_title(title).encode()).hexdigest()


# ─────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(text: str) -> bool:
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(api, json={
            "chat_id": CHANNEL_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        log.warning("Tidak ada koneksi internet.")
        return False
    except Exception as e:
        log.error(f"Telegram error: {e}")
        return False


# ─────────────────────────────────────────────
#  FORMAT PESAN
# ─────────────────────────────────────────────
def bersihkan(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;|&gt;|&nbsp;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_pesan(kategori, sumber, judul, ringkasan, link, pub_time=None) -> str:
    judul     = bersihkan(judul)
    ringkasan = bersihkan(ringkasan)
    if len(ringkasan) > 300:
        ringkasan = ringkasan[:300] + "…"
    wib = datetime.now().strftime("%d %b %Y • %H:%M WIB")
    tag = "#" + re.sub(r"[^a-zA-Z0-9]", "", sumber)

    pub_str = ""
    if pub_time:
        wib_offset = timezone(timedelta(hours=7))
        pt = pub_time.astimezone(wib_offset)
        pub_str = f"📅 <i>Terbit: {pt.strftime('%d %b %Y %H:%M WIB')}</i>\n"

    return (
        f"{kategori}\n"
        f"{'─'*32}\n\n"
        f"📰 <b>{esc(judul)}</b>\n\n"
        f"📝 {esc(ringkasan)}\n\n"
        f"🔗 <a href='{link}'>Baca Selengkapnya »</a>\n\n"
        f"{'─'*32}\n"
        f"🏷 <i>{esc(sumber)}</i>  |  🕐 <i>{wib}</i>\n"
        f"{pub_str}"
        f"{tag} #MarketNews #NewsBot"
    )


# ─────────────────────────────────────────────
#  FETCH & KIRIM
# ─────────────────────────────────────────────
def fetch_and_send():
    log.info("=" * 50)
    log.info(f"Mulai fetch berita (max {MAX_AGE_HOURS} jam terakhir)...")
    seen            = load_seen()
    seen_titles     = set()
    total_sent      = 0
    total_skip_old  = 0
    total_skip_dupl = 0

    for kategori, feeds in SOURCES.items():
        for feed_info in feeds:
            nama = feed_info["name"]
            url  = feed_info["url"]
            try:
                feed    = feedparser.parse(url)
                entries = feed.entries[:MAX_PER_SOURCE]
                for entry in entries:
                    link      = getattr(entry, "link", "")
                    judul     = getattr(entry, "title", "").strip()
                    ringkasan = getattr(entry, "summary", "")
                    if not link or not judul:
                        continue

                    aid = art_id(link)
                    if aid in seen:
                        continue

                    pub_time = parse_published(entry)
                    if not is_recent(entry):
                        seen.add(aid)
                        total_skip_old += 1
                        continue

                    th = title_hash(judul)
                    if th in seen_titles:
                        seen.add(aid)
                        total_skip_dupl += 1
                        log.info(f"Skip (duplikat judul): [{nama}] {judul[:60]}")
                        continue
                    seen_titles.add(th)

                    if not is_relevant(judul + " " + ringkasan):
                        seen.add(aid)
                        continue

                    pesan = format_pesan(kategori, nama, judul, ringkasan, link, pub_time)
                    if send_telegram(pesan):
                        seen.add(aid)
                        total_sent += 1
                        log.info(f"✅ [{nama}] {judul[:60]}...")
                        import time; __import__('time').sleep(DELAY_BETWEEN_SEND)

            except Exception as e:
                log.error(f"Error [{nama}]: {e}")

    save_seen(seen)

    log.info(
        f"Selesai — Terkirim: {total_sent} | "
        f"Skip lama: {total_skip_old} | "
        f"Skip duplikat: {total_skip_dupl}"
    )

    ringkasan_text = (
        f"📊 <b>MARKET BOT — RUN SELESAI</b>\n"
        f"{'─'*28}\n"
        f"✅ <b>{total_sent}</b> berita baru terkirim\n"
        f"⏱ Filter: <b>{MAX_AGE_HOURS} jam</b> terakhir\n"
        f"🚫 Skip lama: {total_skip_old} | Duplikat: {total_skip_dupl}\n"
        f"🕐 {datetime.now().strftime('%d %b %Y %H:%M WIB')}\n"
        f"{'─'*28}\n#BotUpdate"
    )
    send_telegram(ringkasan_text)


# ─────────────────────────────────────────────
#  BRIEFING TERJADWAL
# ─────────────────────────────────────────────
def morning_briefing():
    now  = datetime.now()
    hari = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"][now.weekday()]
    send_telegram(
        f"🌅 <b>MORNING MARKET BRIEFING</b>\n"
        f"{'━'*32}\n"
        f"📅 {hari}, {now.strftime('%d %B %Y')}\n\n"
        f"<b>🔍 Yang Perlu Dipantau:</b>\n"
        f"• Pembukaan pasar Asia (IHSG, Nikkei, HSI)\n"
        f"• Rilis data ekonomi hari ini\n"
        f"• Sentimen Wall Street semalam\n"
        f"• Update Crypto & on-chain data\n"
        f"• Pergerakan USD/IDR\n\n"
        f"📡 Bot memantau <b>{TOTAL_SOURCES} sumber</b> aktif\n"
        f"⏱ Hanya berita <b>{MAX_AGE_HOURS} jam</b> terakhir\n"
        f"{'━'*32}\n"
        f"💡 <i>Stay informed. Trade wisely.</i>\n"
        f"#MorningBriefing #MarketOpen #IHSG"
    )
    log.info("Morning briefing terkirim.")


def closing_summary():
    send_telegram(
        f"🌙 <b>MARKET CLOSING SUMMARY</b>\n"
        f"{'━'*32}\n"
        f"🕔 {datetime.now().strftime('%d %B %Y • %H:%M WIB')}\n\n"
        f"📊 Sesi Asia & Eropa telah ditutup.\n"
        f"🇺🇸 Sesi New York sedang berlangsung.\n"
        f"🪙 Crypto market aktif 24/7.\n\n"
        f"<b>⏰ Jadwal selanjutnya:</b>\n"
        f"• Morning Briefing: 06:00 WIB\n"
        f"• Bot tetap aktif memantau berita\n"
        f"{'━'*32}\n"
        f"#ClosingSummary #IHSG #MarketWrap"
    )
    log.info("Closing summary terkirim.")


# ─────────────────────────────────────────────
#  ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Mode khusus untuk briefing terjadwal via GitHub Actions
    mode = os.environ.get("RUN_MODE", "fetch")

    if mode == "morning":
        morning_briefing()
    elif mode == "closing":
        closing_summary()
    else:
        fetch_and_send()
