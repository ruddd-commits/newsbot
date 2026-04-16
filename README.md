# 📡 Master News Bot — GitHub Actions Edition

Bot Telegram otomatis yang memantau **30+ sumber RSS** dari kategori:
🌍 Internasional · 📈 Saham · 💱 Forex · 🪙 Crypto · 🌐 Makro · 🌍 Geopolitik · 🇮🇩 Indonesia

Berjalan **gratis** di GitHub Actions — tidak perlu server, tidak perlu Termux aktif 24 jam.

---

## 🚀 Cara Deploy (5 Langkah)

### 1. Fork / Clone repo ini ke akun GitHub kamu

```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME
```

### 2. Buat Telegram Bot

1. Buka [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot` → ikuti instruksi → salin **BOT TOKEN**
3. Tambahkan bot sebagai **admin** di channel kamu
4. Salin **Channel ID** (format: `@namachannel` atau `-100xxxxxxxxxx`)

### 3. Tambahkan Secrets di GitHub

Buka repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token dari BotFather |
| `TELEGRAM_CHANNEL_ID` | ID channel Telegram |

### 4. Aktifkan GitHub Actions

Buka tab **Actions** di repo → klik **"I understand my workflows, go ahead and enable them"**

### 5. Jalankan Pertama Kali (Manual)

Buka **Actions** → pilih **"News Bot — Fetch Berita"** → klik **"Run workflow"**

---

## ⏰ Jadwal Otomatis

| Workflow | Jadwal | Keterangan |
|---|---|---|
| `fetch_news.yml` | Setiap 30 menit | Ambil & kirim berita baru |
| `morning_briefing.yml` | 06:00 WIB | Pesan pembuka pasar |
| `closing_summary.yml` | 18:00 WIB | Rekap sesi siang |

> ⚠️ GitHub Actions menggunakan waktu UTC. Jadwal sudah disesuaikan otomatis ke WIB (UTC+7).

---

## ⚙️ Konfigurasi

Edit bagian atas `news_bot.py`:

```python
MAX_AGE_HOURS    = 4   # hanya berita dalam N jam terakhir
MAX_PER_SOURCE   = 20  # maksimum artikel per sumber per run
DELAY_BETWEEN_SEND = 2 # jeda antar pesan (detik)
```

---

## 📁 Struktur File

```
.
├── news_bot.py                        # Script utama
├── requirements.txt                   # Dependensi Python
├── seen_articles.json                 # Cache anti-duplikat (auto-generated)
├── .gitignore
└── .github/
    └── workflows/
        ├── fetch_news.yml             # Fetch berita tiap 30 menit
        ├── morning_briefing.yml       # Briefing pagi 06:00 WIB
        └── closing_summary.yml        # Summary sore 18:00 WIB
```

---

## 🔄 Anti-Duplikat

Bot menggunakan dua lapis perlindungan:
1. **Hash URL** — artikel yang sama tidak dikirim ulang
2. **Hash judul** — berita serupa dari sumber berbeda difilter

Cache disimpan di `seen_articles.json` dan di-commit otomatis ke repo setelah setiap run.

---

## 📝 Catatan

- GitHub Actions gratis untuk repo publik (2.000 menit/bulan untuk repo private)
- Interval minimum cron di GitHub Actions adalah **setiap 5 menit**, bot ini pakai 30 menit
- Jika Actions tidak jalan tepat waktu, itu normal — GitHub kadang delay beberapa menit
