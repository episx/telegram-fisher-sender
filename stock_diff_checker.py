"""
Stock Diff Checker - Yeni Eklenen Hisseleri Tespit Et
stock_lister_fisher.py dosyasini calistirir, onceki liste ile yeni listeyi karsilastirir
ve yeni eklenen hisseleri Telegram ile gonderir.

Kullanim:
    python stock_diff_checker.py
    python stock_diff_checker.py --hisseler BIST100
    python stock_diff_checker.py --chat-id "123456789"
"""

import sys
import argparse
import json
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Sabitler
DEFAULT_PREV_FILE = "data/previous_stocks.json"
DEFAULT_STOCK_LISTER = "stock_lister_fisher.py"
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config" / "telegram.json"


def load_json(filepath: str) -> dict | None:
    """JSON dosyasini oku"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def load_telegram_config() -> dict | None:
    """Telegram config dosyasini oku"""
    return load_json(str(CONFIG_FILE))


def get_stock_list_from_json(data: dict) -> set:
    """JSON verisinden hisse sembollerini al"""
    if not data or "stocks" not in data:
        return set()
    return {item["ticker"] for item in data["stocks"]}


def save_json(filepath: str, data: dict):
    """JSON dosyasina kaydet"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_stock_lister(script_path: str, hisseler: str = "BISTALL", periyot: str = "1mo") -> tuple:
    """stock_lister_fisher.py scriptini calistirir"""
    json_output = SCRIPT_DIR / "data" / "current_scan.json"

    if not os.path.isabs(script_path):
        script_full_path = SCRIPT_DIR / script_path
    else:
        script_full_path = Path(script_path)

    cmd = [
        sys.executable,
        str(script_full_path),
        "--hisseler", hisseler,
        "--periyot", periyot,
        "--json-output", str(json_output)
    ]

    print(f">>> {script_path} calistiriliyor ({hisseler})...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"! Hata: Script calistirilamadi")
        print(f"  stderr: {result.stderr}")
        return None, result.returncode

    data = load_json(json_output)
    return data, 0


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """Telegram ile mesaj gonder"""
    try:
        import requests
    except ImportError:
        print("! requests kutuphanesi yok. pip install requests")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            print(">>> Telegram mesaji gonderildi")
            return True
        else:
            print(f"! Telegram hatasi: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"! Telegram baglanti hatasi: {e}")
        return False


def format_telegram_message(new_stocks: list, removed_stocks: list, current_data: dict, tarih: str) -> str:
    """Telegram mesajini formatla"""
    # Oversold ve Overbought ayir
    oversold = []
    overbought = []

    for stock in current_data.get("stocks", []):
        if stock.get("type") == "oversold":
            oversold.append(stock)
        elif stock.get("type") == "overbought":
            overbought.append(stock)

    # Yeni hisseleri grupla
    new_oversold = [s["ticker"] for s in oversold if s["ticker"] in new_stocks]
    new_overbought = [s["ticker"] for s in overbought if s["ticker"] in new_stocks]

    lines = []
    lines.append(f"*Yeni Fisher Sinyalleri*")
    lines.append(f"Tarih: {tarih}")
    lines.append("")
    lines.append(f"*Toplam: {len(new_stocks)} yeni hisse*")
    lines.append("")

    if new_oversold:
        lines.append(f"*OVERSOLD (Yeni) - {len(new_oversold)} adet*")
        lines.append(", ".join(sorted(new_oversold)))
        lines.append("")

    if new_overbought:
        lines.append(f"*OVERBOUGHT (Yeni) - {len(new_overbought)} adet*")
        lines.append(", ".join(sorted(new_overbought)))
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Yeni Eklenen Hisseleri Tespit Et')
    parser.add_argument('--lister', type=str, default=DEFAULT_STOCK_LISTER,
                        help='Stock lister scripti')
    parser.add_argument('--hisseler', type=str, default='BISTALL',
                        help='Hisse listesi: BIST100, BIST30, BISTALL')
    parser.add_argument('--periyot', type=str, default='1mo',
                        help='Veri periyodu')
    parser.add_argument('--prev', type=str, default=None,
                        help='Onceki liste dosyasi')
    parser.add_argument('--current', type=str, default=None,
                        help='Mevcut scan dosyasi')
    parser.add_argument('--token', type=str, default=None,
                        help='Telegram bot token')
    parser.add_argument('--chat-id', type=str, default=None,
                        help='Telegram chat ID')
    parser.add_argument('--no-save', action='store_true',
                        help='Prev dosyasini guncelleme')
    parser.add_argument('--dry-run', action='store_true',
                        help='Telegram gonderme, sadece konsola yaz')

    args = parser.parse_args()

    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')

    # Telegram config yukle
    telegram_config = load_telegram_config()

    # Token ve chat_id'yi config, ortam degiskenleri veya argumanndan al
    bot_token = (args.token or
                 os.environ.get("BOT_TOKEN") or
                 os.environ.get("TELEGRAM_BOT_TOKEN") or
                 (telegram_config.get("bot_token") if telegram_config else None))

    chat_id = (args.chat_id or
               os.environ.get("CHAT_ID") or
               os.environ.get("TELEGRAM_CHAT_ID") or
               (telegram_config.get("chat_id") if telegram_config else None))

    if not bot_token or not chat_id:
        print("! Telegram ayarlari eksik!")
        print("   config/telegram.json dosyasina bot_token ve chat_id ekleyin")
        print("   veya --token ve --chat-id parametrelerini kullanin")
        return 1

    # Mevcut taramayi al
    if args.current:
        current_data = load_json(args.current)
        if current_data is None:
            print(f"! Hata: {args.current} bulunamadi")
            return 1
    else:
        current_data, rc = run_stock_lister(args.lister, args.hisseler, args.periyot)
        if current_data is None:
            return rc if rc else 1

    current_stocks = get_stock_list_from_json(current_data)
    print(f">>> Mevcut tarama: {len(current_stocks)} hisse")

    # Onceki listeyi yukle
    prev_file = SCRIPT_DIR / args.prev if args.prev else SCRIPT_DIR / "data" / "previous_stocks.json"
    previous_data = load_json(str(prev_file))
    previous_stocks = get_stock_list_from_json(previous_data) if previous_data else set()

    if previous_data:
        print(f">>> Onceki liste: {len(previous_stocks)} hisse")
    else:
        print(f">>> Onceki liste yok - tum hisseler yeni sayilir")

    # Karşılaştır
    new_stocks = current_stocks - previous_stocks
    removed_stocks = previous_stocks - current_stocks

    print("\n" + "="*60)
    print("  KARSILASTIRMA SONUCU")
    print("="*60)
    print(f"  Tarih: {tarih}")
    print(f"  Onceki: {len(previous_stocks)} | Mevcut: {len(current_stocks)}")
    print("="*60)

    if new_stocks:
        print(f"\n[YENI HİSSELER] ({len(new_stocks)} adet)")
        print("-"*60)
        for hisse in sorted(new_stocks):
            print(f"  + {hisse}")
    else:
        print("\n[YENI HİSSELER] : yok")

    if removed_stocks:
        print(f"\n[CIKARILAN HİSSELER] ({len(removed_stocks)} adet)")
        for hisse in sorted(removed_stocks):
            print(f"  - {hisse}")

    # Telegram mesaji gonder
    if new_stocks:
        message = format_telegram_message(list(new_stocks), list(removed_stocks), current_data, tarih)

        if args.dry_run:
            print("\n>>> [DRY RUN] Telegram mesaji:")
            print("-"*60)
            print(message)
            print("-"*60)
        else:
            success = send_telegram_message(bot_token, chat_id, message)
            if not success:
                print("! Telegram mesaji gonderilemedi")
    else:
        print("\n>>> Yeni hisse yok, Telegram mesaji gonderilmedi")

    # Previous listeyi guncelle
    if not args.no_save:
        save_json(str(prev_file), current_data)
        print(f">>> Previous liste guncellendi: {prev_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())