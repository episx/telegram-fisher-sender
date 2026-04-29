"""
STRATEJİ DOSYASI KALIBI
============================================

python "C:\Users\HP\OneDrive\Desktop\Trading test2\backtest_sistemi\backtest_kalıp.py" stratejiler/strateji_kalıp.py

============================================
STRATEJİ TANIMI
# Hisse: THYAO.IS
# Başlangıç: 2024-01-01
# Bitiş: 2024-12-31
# Timeframe: 1d
# İndikatörler: RSI, MACD, EMA

# ============================================
# STRATEJİ PARAMETRELERİ
# ============================================

# --- Trigger Conditions (Giriş Koşulları) ---
# RSI < 30 VE MACD histogramı > 0
# Fiyat EMA(20) üzerinde

# --- Take Profit ---
# TP1: %3
# TP2: %5
# TP1 için %50 pozisyon kapatılır

# --- Stop Loss ---
# Sabit %2 stop loss

# --- İşlem Kapatma Koşulları ---
# Fiyat EMA(50) altına düştüğünde sat
# RSI > 70 olduğunda sat

# --- Pozisyon Büyüklüğü ---
# ATR bazlı: Risk = %2, ATR * 1.5
# Minimum pozisyon: 1000 TL
# Maksimum pozisyon: sermaye * 0.1

# ============================================
# ÇALIŞTIRMA KOMUTU
# ============================================
# Bu stratejiyi çalıştırmak için:
# python backtest_template.py stratejiler/THYAO_RSI_MACD_EMA.py

"""

# ============================================
# STRATEJİ PARAMETRELERİ - DÜZENLENECEK
# ============================================

STRATEJİ_ADI = "RSI_MACD_EMA_Stratejisi"
HİSSE = "THYAO.IS"
BAŞLANGIÇ_TARİHİ = "2024-01-01"
BİTİŞ_TARİHİ = "2024-12-31"
TIMEFRAME = "1d"

# Kullanılacak İndikatörler ve Parametreleri
İNDİKATÖRLER = {
    'RSI': {'periyot': 14, 'astigi': 30, 'yukari': 70},
    'MACD': {'hizli_per': 12, 'yavas_per': 26, 'sinyal_per': 9},
    'EMA': {'periyot': 20}
}

# Giriş Koşulları (trigger conditions)
GİRİŞ_KOŞULLARI = {
    'RSI_koşul': '<',  # değer veya formül
    'RSI_değer': 30,
    'MACD_koşul': '>',  # histogram > 0
    'MACD_değer': 0,
    'EMA_koşul': 'fiyat_üzerinde',  # fiyat EMA üzerinde
}

# Take Profit
TAKE_PROFIT = [
    {'seviye': 1, 'yüzde': 3, 'kapatılacak': 0.50},  # %3'te %50 kapat
    {'seviye': 2, 'yüzde': 5, 'kapatılacak': 1.00}   # %5'te kalan %50 kapat
]

# Stop Loss
STOP_LOSS = {'yüzde': 2, 'tip': 'sabit'}

# İşlem Kapatma Koşulları (Exit)
ÇIKIŞ_KOŞULLARI = [
    {'koşul': 'fiyat_EMA_altında', 'EMA_periyot': 50},
    {'koşul': 'RSI_yukari', 'RSI_değer': 70}
]

# Pozisyon Büyüklüğü
POZİSYON = {
    'hesaplama': 'ATR_bazlı',
    'risk_yüzdesi': 2.0,
    'ATR_çarpanı': 1.5,
    'minimum': 1000,
    'maksimum_oran': 0.1  # sermayenin %10'u
}

# ============================================
# KOŞUL FONKSİYONLARI
# ============================================

def giriş_sinyali(data: dict) -> bool:
    """
    Giriş sinyali verilip verilmediğini kontrol eder.
    data: Tüm indikatör değerlerini içeren dict
    """
    rsi = data.get('RSI', 50)
    macd_hist = data.get('MACD_histogram', 0)
    ema = data.get('EMA', 0)
    fiyat = data.get('fiyat', 0)

    # RSI < 30 VE MACD histogramı > 0 VE fiyat EMA üzerinde
    if rsi < 30 and macd_hist > 0 and fiyat > ema:
        return True
    return False


def çıkış_sinyali(data: dict) -> tuple:
    """
    Çıkış sinyali verilip verilmediğini kontrol eder.
    Dönüş: (sinyal: bool, neden: str)
    """
    ema50 = data.get('EMA50', 0)
    fiyat = data.get('fiyat', 0)
    rsi = data.get('RSI', 50)

    if fiyat < ema50:
        return True, "Fiyat EMA(50) altında"
    if rsi > 70:
        return True, "RSI > 70"
    return False, ""


def tp_sinyali(data: dict, tp_seviyesi: float) -> bool:
    """
    Take profit sinyali kontrolü.
    """
    kar_yüzdesi = data.get('açık_kar_yüzdesi', 0)
    return kar_yüzdesi >= tp_seviyesi
