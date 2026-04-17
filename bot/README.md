# 303 Discord Bot (Python)

## Kurulum

### 1. Python 3.10+ yüklü olduğundan emin ol

### 2. Bağımlılıkları yükle
```bash
cd bot
pip install -r requirements.txt
```

### 3. .env dosyasını oluştur
```bash
cp .env.example .env
```
`.env` dosyasını aç ve `TOKEN` kısmına Discord bot tokenini yapıştır.

### 4. 303 logosunu ekle
`bot/assets/logo.png` dosyasına 303 logonu koy.

### 5. Botu başlat
```bash
python main.py
```

---

## Komutlar

| Komut | Açıklama | Yetki |
|-------|----------|-------|
| `/stat [@kullanıcı]` | İstatistikleri gösterir | Herkes |
| `/unban <id> [sebep]` | Kullanıcının banını kaldırır | Ban Members |
| `/ticket-panel` | Ticket panelini gönderir | Administrator |

---

## Dosya Yapısı
```
bot/
├── cogs/
│   ├── ticket.py    → Ticket sistemi
│   ├── stat.py      → İstatistik komutu + mesaj/ses takibi
│   └── unban.py     → Unban komutu
├── utils/
│   └── db.py        → JSON veritabanı
├── assets/
│   └── logo.png     → 303 logosu (kendin ekle)
├── data/
│   └── stats.json   → İstatistik verileri (otomatik oluşur)
├── main.py
├── requirements.txt
└── .env
```

---

## Bot Yetkileri
Discord Developer Portal'da bota şu yetkileri ver:
- `Send Messages`
- `Manage Channels`
- `Ban Members`
- `View Channels`
- `Read Message History`

Intents kısmında şunları aç:
- `Server Members Intent`
- `Message Content Intent`
