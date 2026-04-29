"""
BACKTEST KALIP DOSYASI
======================

Bu dosya, strateji dosyaları ve indikatör dosyaları ile birlikte çalışır.
Bir strateji dosyası ile birleştirildiğinde:
1. Stratejide belirtilen indikatörleri okur ve indikatör dosyalarından nasıl hesaplandığını alır
2. Backtest için gerekli verileri import eder
3. Stratejiyi test eder
4. Sonuçları yazdırır

Kullanım:
    python backtest_kalıp.py strateji_dosyası.py [--sermaye SERMAYE] [--veri VERİ_DOSYASI]
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

# Script dizini
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# İndikatör modülünü import et
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'indikatörler'))
import indikatörler


# ============================================
# VERİ YAPILARI
# ============================================

@dataclass
class İşlem:
    """Tek bir işlemi temsil eder."""
    tarih: str
    tip: str  # 'LONG' veya 'SHORT'
    fiyat: float
    miktar: float
    tp_seviyesi: list
    sl_seviyesi: float
    kapanış_tarihi: Optional[str] = None
    kapanış_fiyatı: Optional[float] = None
    kapanış_nedeni: Optional[str] = None
    kar_zarar: float = 0.0
    kar_zarar_yüzdesi: float = 0.0


@dataclass
class BacktestSonuçları:
    """Backtest sonuçlarını tutar."""
    toplam_işlem: int = 0
    kazanan_işlem: int = 0
    kaybeden_işlem: int = 0
    winrate: float = 0.0
    toplam_kar_zarar: float = 0.0
    toplam_kar_zarar_yüzdesi: float = 0.0
    maks_kar_yüzdesi: float = 0.0
    maks_zarar_yüzdesi: float = 0.0
    işlem_listesi: list = field(default_factory=list)


# ============================================
# BACKTEST MOTORU
# ============================================

class BacktestMotoru:
    """Backtest motoru - stratejiyi test eder."""

    def __init__(self, strateji_modülü, veri: pd.DataFrame, sermaye: float = 100000):
        self.strateji = strateji_modülü
        self.veri = veri
        self.sermaye = sermaye
        self.bakiye = sermaye
        self.açık_işlem: Optional[İşlem] = None
        self.sonuçlar = BacktestSonuçları()
        self.indikatör_değerleri = {}

    def _indikatörleri_hesapla(self):
        """Stratejide belirtilen indikatörleri hesaplar."""
        indikatörler_config = self.strateji.İNDİKATÖRLER
        self.indikatör_değerleri = {'fiyat': self.veri['close']}

        # İndikatör hesaplama parametreleri (sadece gerekli olanları gönder)
        for ind_name, params in indikatörler_config.items():
            if ind_name == 'RSI':
                # Sadece periyot parametresini gönder
                rsi_params = {k: v for k, v in params.items() if k == 'periyot'}
                self.indikatör_değerleri['RSI'] = indikatörler.rsi_hesapla(self.veri, **rsi_params)
            elif ind_name == 'MACD':
                macd_params = {k: v for k, v in params.items() if k in ['hizli_per', 'yavas_per', 'sinyal_per']}
                macd = indikatörler.macd_hesapla(self.veri, **macd_params)
                self.indikatör_değerleri['MACD'] = macd['macd']
                self.indikatör_değerleri['MACD_sinyal'] = macd['sinyal']
                self.indikatör_değerleri['MACD_histogram'] = macd['histogram']
            elif ind_name == 'EMA':
                ema_params = {k: v for k, v in params.items() if k == 'periyot'}
                self.indikatör_değerleri['EMA'] = indikatörler.ema_hesapla(self.veri, **ema_params)

        # Çıkış için gerekli EMA50 hesapla (opsiyonel)
        if any('EMA' in str(c.get('koşul', '')) for c in self.strateji.ÇIKIŞ_KOŞULLARI):
            self.indikatör_değerleri['EMA50'] = indikatörler.ema_hesapla(self.veri, periyot=50)

    def _pozisyon_hesapla(self, fiyat: float, atr: float = None) -> float:
        """Pozisyon büyüklüğünü hesaplar."""
        poz_cfg = self.strateji.POZİSYON
        min_poz = poz_cfg.get('minimum', 1000)
        maks_oran = poz_cfg.get('maksimum_oran', 0.1)

        if poz_cfg['hesaplama'] == 'ATR_bazlı':
            risk_amount = self.sermaye * (poz_cfg['risk_yüzdesi'] / 100)
            atr_değeri = atr if atr is not None else fiyat * 0.02
            poz_büyüklüğü = risk_amount / (atr_değeri * poz_cfg.get('ATR_çarpanı', 1.5))
        else:
            poz_büyüklüğü = self.sermaye * maks_oran

        poz_büyüklüğü = max(min_poz, min(poz_büyüklüğü, self.sermaye * maks_oran))
        return poz_büyüklüğü / fiyat  # Lot olarak döndür

    def _işlem_kapat(self, tarih: str, fiyat: float, neden: str):
        """Açık işlemi kapatır."""
        if self.açık_işlem is None:
            return

        işlem = self.açık_işlem
        işlem.kapanış_tarihi = tarih
        işlem.kapanış_fiyatı = fiyat
        işlem.kapanış_nedeni = neden

        # Kar/Zarar hesapla (LONG pozisyon için)
        if işlem.tip == 'LONG':
            işlem.kar_zarar = (fiyat - işlem.fiyat) * işlem.miktar
            işlem.kar_zarar_yüzdesi = ((fiyat - işlem.fiyat) / işlem.fiyat) * 100
        else:
            işlem.kar_zarar = (işlem.fiyat - fiyat) * işlem.miktar
            işlem.kar_zarar_yüzdesi = ((işlem.fiyat - fiyat) / işlem.fiyat) * 100

        self.bakiye += işlem.kar_zarar
        self.sonuçlar.işlem_listesi.append(işlem)
        self.açık_işlem = None

    def _işlem_aç(self, tarih: str, fiyat: float, tp_list: list, sl_seviyesi: float):
        """Yeni işlem açar."""
        miktar = self._pozisyon_hesapla(fiyat)
        self.açık_işlem = İşlem(
            tarih=tarih,
            tip='LONG',
            fiyat=fiyat,
            miktar=miktar,
            tp_seviyesi=tp_list,
            sl_seviyesi=sl_seviyesi
        )

    def çalıştır(self):
        """Backtest'i çalıştırır."""
        self._indikatörleri_hesapla()

        for i in range(len(self.veri)):
            tarih = self.veri.index[i]
            fiyat = self.veri['close'].iloc[i]

            # Mevcut indikatör değerlerini al
            data = {k: v.iloc[i] if hasattr(v, 'iloc') else v
                   for k, v in self.indikatör_değerleri.items()}

            if self.açık_işlem is None:
                # Giriş sinyali kontrolü
                if self.strateji.giriş_sinyali(data):
                    tp = [tp['yüzde'] for tp in self.strateji.TAKE_PROFIT]
                    sl = self.strateji.STOP_LOSS['yüzde']
                    self._işlem_aç(str(tarih), fiyat, tp, sl)
            else:
                # Açık işlem yönetimi
                işlem = self.açık_işlem
                kar_yüzdesi = ((fiyat - işlem.fiyat) / işlem.fiyat) * 100
                data['açık_kar_yüzdesi'] = kar_yüzdesi

                # Stop Loss kontrolü
                if kar_yüzdesi <= -işlem.sl_seviyesi:
                    self._işlem_kapat(str(tarih), fiyat, "Stop Loss")
                    continue

                # TP kontrolü
                for tp in self.strateji.TAKE_PROFIT:
                    if kar_yüzdesi >= tp['yüzde']:
                        # Kısmi kapatma simülasyonu (sadece tamamını kapatıyoruz)
                        self._işlem_kapat(str(tarih), fiyat, f"Take Profit %{tp['yüzde']}")
                        break

                # Çıkış sinyali kontrolü
                çıkış, neden = self.strateji.çıkış_sinyali(data)
                if çıkış:
                    self._işlem_kapat(str(tarih), fiyat, neden)

        # Açık işlem varsa son fiyattan kapat
        if self.açık_işlem is not None:
            son_fiyat = self.veri['close'].iloc[-1]
            son_tarih = self.veri.index[-1]
            self._işlem_kapat(str(son_tarih), son_fiyat, "Backtest Sonu")

        self._sonuçları_hesapla()

    def _sonuçları_hesapla(self):
        """Sonuçları hesaplar ve saklar."""
        işlemler = self.sonuçlar.işlem_listesi

        if not işlemler:
            return

        self.sonuçlar.toplam_işlem = len(işlemler)
        self.sonuçlar.kazanan_işlem = sum(1 for i in işlemler if i.kar_zarar > 0)
        self.sonuçlar.kaybeden_işlem = sum(1 for i in işlemler if i.kar_zarar <= 0)
        self.sonuçlar.winrate = (self.sonuçlar.kazanan_işlem / self.sonuçlar.toplam_işlem) * 100

        kar_zararlar = [i.kar_zarar_yüzdesi for i in işlemler]
        self.sonuçlar.toplam_kar_zarar = sum(kar_zararlar)
        self.sonuçlar.toplam_kar_zarar_yüzdesi = sum(kar_zararlar)
        self.sonuçlar.maks_kar_yüzdesi = max(kar_zararlar) if kar_zararlar else 0
        self.sonuçlar.maks_zarar_yüzdesi = min(kar_zararlar) if kar_zararlar else 0

    def yazdır(self):
        """Sonuçları yazdırır."""
        s = self.sonuçlar
        print("\n" + "=" * 60)
        print(f"BACKTEST SONRÇLARI - {self.strateji.STRATEJİ_ADI}")
        print("=" * 60)
        print(f"Hisse: {self.strateji.HİSSE}")
        print(f"Tarih Aralığı: {self.strateji.BAŞLANGIÇ_TARİHİ} - {self.strateji.BİTİŞ_TARİHİ}")
        print(f"Sermaye: {self.sermaye:,.2f} TL")
        print("-" * 60)
        print(f"Toplam İşlem: {s.toplam_işlem}")
        print(f"Kazanan: {s.kazanan_işlem} | Kaybeden: {s.kaybeden_işlem}")
        print(f"Winrate: {s.winrate:.2f}%")
        print("-" * 60)
        print(f"Toplam Kar/Zarar: {s.toplam_kar_zarar:,.2f} TL")
        print(f"Toplam Kar/Zarar %: {s.toplam_kar_zarar_yüzdesi:.2f}%")
        print(f"Maksimum Kar %: {s.maks_kar_yüzdesi:.2f}%")
        print(f"Maksimum Zarar %: {s.maks_zarar_yüzdesi:.2f}%")
        print("=" * 60)
        print("\nYAPILAN İŞLEMLER:")
        print("-" * 120)
        print(f"{'Tarih':<12} {'Tip':<6} {'Fiyat':<10} {'Miktar':<10} {'Kar/Zarar':<12} {'%':<8} {'Kapanış':<12} {'Neden'}")
        print("-" * 120)
        for i in s.işlem_listesi:
            print(f"{i.tarih:<12} {i.tip:<6} {i.fiyat:<10.2f} {i.miktar:<10.4f} "
                  f"{i.kar_zarar:<12.2f} {i.kar_zarar_yüzdesi:<8.2f} {i.kapanış_nedeni}")
        print("-" * 120)


# ============================================
# VERİ İMPORT
# ============================================

def veri_import_et(hisse: str, başlangıç: str, bitiş: str, timeframe: str) -> pd.DataFrame:
    """
    Backtest için veri import eder.
    Yahoo Finance'ten gerçek veri çeker.
    """
    import yfinance as yf

    print(f"Veri import ediliyor: {hisse} ({başlangıç} - {bitiş})")

    # Yahoo Finance'den veri çek
    ticker = yf.Ticker(hisse)
    veri = ticker.history(start=başlangıç, end=bitiş, interval='1d')

    if veri.empty:
        raise ValueError(f"Veri bulunamadı: {hisse} ({başlangıç} - {bitiş})")

    # Sütun isimlerini standartlaştır
    veri.columns = [col.lower() for col in veri.columns]

    print(f"Veri import edildi: {len(veri)} satır")
    return veri


# ============================================
# ANA ÇALIŞTIRICI
# ============================================

def main():
    parser = argparse.ArgumentParser(description='Backtest Motoru')
    parser.add_argument('strateji_dosyası', help='Strateji Python dosyası')
    parser.add_argument('--sermaye', type=float, default=100000, help='Başlangıç sermayesi')
    parser.add_argument('--veri', type=str, default=None, help='Veri dosyası (opsiyonel)')

    args = parser.parse_args()

    # Stratejiyi import et
    import importlib.util

    # Dosya yolunu script dizinine göre çözümle
    strateji_yolu = args.strateji_dosyası

    if not os.path.isabs(strateji_yolu):
        strateji_yolu = os.path.join(SCRIPT_DIR, strateji_yolu)

    spec = importlib.util.spec_from_file_location("strateji", strateji_yolu)
    strateji_modülü = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strateji_modülü)

    # Veriyi al
    veri = veri_import_et(
        strateji_modülü.HİSSE,
        strateji_modülü.BAŞLANGIÇ_TARİHİ,
        strateji_modülü.BİTİŞ_TARİHİ,
        strateji_modülü.TIMEFRAME
    )

    # Backtest'i çalıştır
    motor = BacktestMotoru(strateji_modülü, veri, args.sermaye)
    motor.çalıştır()
    motor.yazdır()


if __name__ == "__main__":
    main()
