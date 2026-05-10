# Stock Diff Checker

Bu proye yeni eklenen hisseleri tespit eder ve Telegram üzerinden bildirim gönderir.

## Kurulum

### Yerel Kullanım

1. Gerekli Python paketlerini yükleyin:
```bash
pip install requests
```

2. Telegram bot ayarlarını yapılandırın:

**Seçenek A: Config dosyası (önerilen)**
```bash
cp config/telegram.json.example config/telegram.json
```
Sonra `config/telegram.json` dosyasını düzenleyin.

**Seçenek B: Ortam değişkenleri**
```bash
export BOT_TOKEN="your_bot_token_here"
export CHAT_ID="your_chat_id_here"
```

### GitHub Actions ile Otomatik Çalıştırma

1. Repository Settings -> Secrets and variables -> Actions bölümünde şu secrets'ı ekleyin:
   - `BOT_TOKEN`: Telegram bot token'ınız
   - `CHAT_ID`: Telegram chat ID'niz

2. GitHub Actions workflow'u otomatik olarak çalışacaktır.

## Kullanım

```bash
# Temel kullanım
python stock_diff_checker.py

# Belirli hisse grubu için
python stock_diff_checker.py --hisseler BIST100

# Dry run (telegram'a göndermeden test et)
python stock_diff_checker.py --dry-run

# Manuel token ve chat ID
python stock_diff_checker.py --token "YOUR_TOKEN" --chat-id "YOUR_CHAT_ID"
```

## Ortam Değişkenleri

Script aşağıdaki sırayla ayarları arar:

1. Command line parametreleri (`--token`, `--chat-id`)
2. Ortam değişkenleri:
   - `BOT_TOKEN` veya `TELEGRAM_BOT_TOKEN`
   - `CHAT_ID` veya `TELEGRAM_CHAT_ID`
3. Config dosyası (`config/telegram.json`)

## GitHub Actions Sorun Giderme

Eğer GitHub Actions'da "bot token eksik" hatası alıyorsanız:

1. Repository Settings -> Secrets and variables -> Actions'da `BOT_TOKEN` ve `CHAT_ID` secrets'ının ekli olduğundan emin olun
2. Workflow dosyasında bu secrets'ın ortam değişkeni olarak tanımlandığından emin olun:
   ```yaml
   env:
     BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
     CHAT_ID: ${{ secrets.CHAT_ID }}
   ```