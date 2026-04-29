"""
Telegram Fisher Bot - Her gun saat 19:00 UTC+3'de calisir
stock_lister_fisher.py calistirir ve ciktisini Telegram'dan gonderir.

Yapilandirma:
    1. .env dosyasi olusturun (ayarlar.env örnegi icin bkz.)
    2. VEYA ortam degiskenlerini ayarlayin:
       TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

Kullanim:
    python telegram_fisher_sender.py
"""

import subprocess
import sys
import os
from datetime import datetime
import urllib.request
import urllib.error
import json
from pathlib import Path

# .env dosyasindan ortam degiskenlerini yukle
def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()


class TelegramSender:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f'https://api.telegram.org/bot{bot_token}'

    def send_message(self, text: str, parse_mode='Markdown') -> bool:
        url = f'{self.api_url}/sendMessage'
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
        }
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
        except urllib.error.HTTPError as e:
            print(f"HTTP Hatasi: {e.code} - {e.read().decode('utf-8')}")
            return False
        except urllib.error.URLError as e:
            print(f"URL Hatasi: {e.reason}")
            return False
        except Exception as e:
            print(f"Gonderim Hatasi: {e}")
            return False


def run_fisher_script() -> tuple:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'stock_lister_fisher.py')

    if not os.path.exists(script_path):
        return '', f"Script bulunamadi: {script_path}"

    python_path = os.path.join(script_dir, '.venv', 'Scripts', 'python.exe')
    if not os.path.exists(python_path):
        python_path = sys.executable

    try:
        result = subprocess.run(
            [python_path, script_path],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=script_dir
        )
        output = result.stdout + result.stderr
        return output, ''
    except subprocess.TimeoutExpired:
        return '', "Script timeout oldu (10 dakika)"
    except Exception as e:
        return '', f"Script calistirma hatasi: {e}"


def filter_output(text: str) -> str:
    lines = text.split('\n')
    filtered = []
    skip_keywords = ['[DEBUG]', 'Satir sayisi:', 'Sutunlar:', '>>> Fisher Transform hesaplaniyor']
    for line in lines:
        if any(kw in line for kw in skip_keywords):
            continue
        filtered.append(line)
    return '\n'.join(filtered)


def split_fisher_output(text: str) -> tuple:
    """Fisher ciktisini oversold ve overbought olarak ayirir"""
    lines = text.split('\n')
    oversold_lines = []
    overbought_lines = []
    current_section = None

    for line in lines:
        if '[OVERSOLD]' in line:
            current_section = 'oversold'
        elif '[OVERBOUGHT]' in line:
            current_section = 'overbought'
        elif 'OZET:' in line or '=' * 60 in line:
            current_section = None
        elif current_section == 'oversold':
            oversold_lines.append(line)
        elif current_section == 'overbought':
            overbought_lines.append(line)

    return '\n'.join(oversold_lines), '\n'.join(overbought_lines)


def main():
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '').strip()

    if not bot_token:
        print("Hata: TELEGRAM_BOT_TOKEN ortam degiskeni tanimlanmamis.")
        sys.exit(1)
    if not chat_id:
        print("Hata: TELEGRAM_CHAT_ID ortam degiskeni tanimlanmamis.")
        sys.exit(1)

    print(f"[{datetime.now():%d.%m.%Y %H:%M}] Fisher tarama basliyor...")

    output, error = run_fisher_script()
    output = filter_output(output)

    if error:
        print(f"Hata: {error}")
        sys.exit(1)

    telegram = TelegramSender(bot_token, chat_id)
    tarih = datetime.now().strftime('%d.%m.%Y')

    oversold_text, overbought_text = split_fisher_output(output)

    print(f"[DEBUG] Oversold lines: {len(oversold_text)} chars, Overbought lines: {len(overbought_text)} chars")
    print(f"[DEBUG] Raw output sample (first 500):\n{output[:500]}")

    baslik_oversold = f"*Fisher Transform Tarama - {tarih}\nOVERSOLD (Alim sinyali)*"
    baslik_overbought = f"*Fisher Transform Tarama - {tarih}\nOVERBOUGHT (Satis sinyali)*"

    # OVERSOLD gonder
    if oversold_text.strip():
        msg = f"{baslik_oversold}\n\n{oversold_text}"
        if len(msg) > 4096:
            msg = msg[:4096 - 100] + "\n\n_[... mesaj kesildi]_"
        print(f"[OVERSOLD] Mense gonderiliyor ({len(msg)} karakter)...")
        if not telegram.send_message(msg):
            print("OVERSOLD gonderim basarisiz.")
            sys.exit(1)
    else:
        telegram.send_message(f"{baslik_oversold}\n\n_Hic hisse bulunamadi_")

    # OVERBOUGHT gonder
    if overbought_text.strip():
        msg = f"{baslik_overbought}\n\n{overbought_text}"
        if len(msg) > 4096:
            msg = msg[:4096 - 100] + "\n\n_[... mesaj kesildi]_"
        print(f"[OVERBOUGHT] Mense gonderiliyor ({len(msg)} karakter)...")
        if not telegram.send_message(msg):
            print("OVERBOUGHT gonderim basarisiz.")
            sys.exit(1)
    else:
        telegram.send_message(f"{baslik_overbought}\n\n_Hic hisse bulunamadi_")

    print("Basariyla gonderildi!")


if __name__ == '__main__':
    main()
