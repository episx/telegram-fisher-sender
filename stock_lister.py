"""
Stock Lister - Koşullara göre stock listeleme
Kullanım:
    python stock_lister.py --hisseler bist100 --indikatör fisher --koşul "fisher <= -1.5 or fisher >= 1.5"
    python stock_lister.py --hisseler THYAO,ASELS,GARAN --indikatör rsi --koşul "rsi < 30"
"""

import argparse
import sys
from datetime import datetime
import pandas as pd
import numpy as np

from borsa_listesi import BIST100_HISSE, BIST30
from indikatörler import (
    fisher_hesapla, fisher_sinyal,
    williams_r_hesapla, williams_r_sinyal,
    adx_hesapla, adx_sinyal,
    rsi_hesapla, rsi_sinyal,
    sma_hesapla, ema_hesapla, macd_hesapla
)


class StockDataFetcher:
    """Stock verisi çekici (yfinance kullanarak)"""

    @staticmethod
    def veri_çek(hisse_listesi: list, periyot: str = '1y', batch_size: int = 50) -> dict:
        """
        Hisse verilerini çeker - TOPLU İNDİRME.
        """
        try:
            import yfinance as yf
        except ImportError:
            print("yfinance kurulu değil. pip install yfinance ile kurun.")
            sys.exit(1)

        veriler = {}
        hata_listesi = []

        # .IS suffix ekle ve listeyi hazırla
        yf_semboller = [f"{h}.IS" for h in hisse_listesi]

        print(f"[{len(yf_semboller)} hisse] Toplu indirme basliyor...")

        # Batch'ler halinde indir
        for i in range(0, len(yf_semboller), batch_size):
            batch = yf_semboller[i:i + batch_size]
            print(f"  Batch {i // batch_size + 1}: {batch[0]} ... {batch[-1]} ({len(batch)} hisse)")

            try:
                # Toplu indirme
                data = yf.download(
                    batch,
                    period=periyot,
                    interval="1d",
                    group_by="ticker",
                    auto_adjust=True,
                    threads=True,
                    progress=False
                )

                if data.empty:
                    print(f"  Batch {i // batch_size + 1}: Bos veri")
                    continue

                # Her hisse için ayrı DataFrame'e çevir
                for hisse in batch:
                    sembol = hisse.replace(".IS", "")
                    try:
                        # xs ile hisse verisini çıkar
                        hisse_df = data.xs(hisse, level=0, axis=1)

                        if hisse_df.empty:
                            hata_listesi.append((sembol, 'bos veri'))
                            continue

                        # Sütun isimlerini küçük harfe çevir
                        hisse_df.columns = [c.lower() for c in hisse_df.columns]
                        veriler[sembol] = hisse_df

                    except Exception as e:
                        hata_listesi.append((sembol, str(e)[:50]))

            except Exception as e:
                print(f"  Batch {i // batch_size + 1} hatası: {e}")

        print(f"[OK] {len(veriler)}/{len(hisse_listesi)} hisse verisi alindi")
        if hata_listesi:
            print(f"[!] {len(hata_listesi)} hisse hatali (ornek: {hata_listesi[0]})")

        return veriler

        return veriler


class IndicatorEvaluator:
    """İndikatör değerlendirici"""

    @staticmethod
    def hesapla_indikatör(data: pd.DataFrame, indikatör: str) -> pd.Series:
        """Belirtilen indikatörü hesaplar"""
        if indikatör == 'fisher':
            return fisher_hesapla(data)
        elif indikatör == 'williams_r':
            return williams_r_hesapla(data)
        elif indikatör == 'adx':
            return adx_hesapla(data)['adx']
        elif indikatör == 'rsi':
            return rsi_hesapla(data)
        elif indikatör == 'macd':
            return macd_hesapla(data)['histogram']
        else:
            raise ValueError(f"Bilinmeyen indikatör: {indikatör}")

    @staticmethod
    def koşul_değerlendir(değer: float, koşul: str) -> bool:
        """Koşulu değerlendirir"""
        try:
            # Güvenli değerlendirme - sadece sayısal karşılaştırma
            if 'and' in koşul.lower():
                parts = koşul.lower().split('and')
                return all(IndicatorEvaluator.koşul_değerlendir(değer, p.strip()) for p in parts)
            elif 'or' in koşul.lower():
                parts = koşul.lower().split('or')
                return any(IndicatorEvaluator.koşul_değerlendir(değer, p.strip()) for p in parts)

            # Temel karşılaştırma operatörleri
            operators = ['<=', '>=', '==', '!=', '<', '>', '=']
            for op in operators:
                if op in koşul:
                    left, right = koşul.split(op, 1)
                    left = left.strip()
                    right = right.strip()

                    if right.lstrip('-').replace('.', '').isdigit():
                        right = float(right)
                        değer_float = float(değer)
                    else:
                        return False  # Bilinmeyen değişken

                    if op == '<=':
                        return değer_float <= right
                    elif op == '>=':
                        return değer_float >= right
                    elif op == '==':
                        return değer_float == right
                    elif op == '!=':
                        return değer_float != right
                    elif op == '<':
                        return değer_float < right
                    elif op == '>':
                        return değer_float > right
                    elif op == '=':
                        return değer_float == right

            return False
        except Exception as e:
            print(f"Koşul değerlendirme hatası: {e}")
            return False


class StockLister:
    """Stock listeleyici sınıfı"""

    def __init__(self, veriler: dict):
        self.veriler = veriler

    def filtrele(self, indikatör: str, koşul: str, son_bar: int = 0) -> dict:
        """
        Koşula uyan hisseleri filtreler.

        Parametreler:
            indikatör: Hesaplanacak indikatör
            koşul: Koşul stringi (örn: "fisher <= -1.5 or fisher >= 1.5")
            son_bar: Kaçıncı bar (0 = son güncel)

        Dönüş:
            dict: {hisse: indikatör_değeri}
        """
        sonuçlar = {}

        for hisse, data in self.veriler.items():
            try:
                ind_val = IndicatorEvaluator.hesapla_indikatör(data, indikatör)

                if son_bar == 0:
                    değer = ind_val.iloc[-1]
                else:
                    değer = ind_val.iloc[son_bar]

                if pd.isna(değer):
                    continue

                if IndicatorEvaluator.koşul_değerlendir(değer, koşul):
                    sonuçlar[hisse] = {
                        'değer': değer,
                        'veri_boyutu': len(data)
                    }

            except Exception as e:
                print(f"{hisse} değerlendirilirken hata: {e}")

        return sonuçlar

    def rapor_yazdır(self, sonuçlar: dict, indikatör: str, koşul: str):
        """Sonuçları rapor olarak yazdırır"""
        print("\n" + "="*60)
        print(f"STOCK LISTER RAPORU")
        print(f"İndikatör: {indikatör.upper()}")
        print(f"Koşul: {koşul}")
        print("="*60)

        if not sonuçlar:
            print("\n! Hicbir hisse kosulu saglamadi.")
            return

        print(f"\nOK - {len(sonuçlar)} hisse kosulu sagladi:\n")
        print(f"{'Hisse':<10} {'Değer':>12} {'Veri Boyutu':>12}")
        print("-"*36)

        # Değere göre sırala
        sıralı = sorted(sonuçlar.items(), key=lambda x: x[1]['değer'], reverse=True)
        for hisse, bilgi in sıralı:
            print(f"{hisse:<10} {bilgi['değer']:>12.4f} {bilgi['veri_boyutu']:>12}")

        print("-"*36)
        print(f"Toplam: {len(sonuçlar)} hisse")
        print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(description='Stock Lister - Koşullara göre hisse listeleme')
    parser.add_argument('--hisseler', type=str, required=True,
                        help='Hisse listesi (virgülle ayrılmış) veya endeks adı (bist100, bist30)')
    parser.add_argument('--indikatör', type=str, required=True,
                        help='İndikatör (fisher, rsi, williams_r, adx, macd)')
    parser.add_argument('--koşul', type=str, required=True,
                        help='Koşul (örn: "fisher <= -1.5 or fisher >= 1.5")')
    parser.add_argument('--periyot', type=str, default='3mo',
                        help='Veri periyodu (1mo, 3mo, 6mo, 1y)')
    parser.add_argument('--çıktı', type=str, default=None,
                        help='Sonuçları dosyaya kaydet')

    args = parser.parse_args()

    # Hisse listesini belirle
    hisse_giriş = args.hisseler.upper().strip()

    if hisse_giriş == 'BIST100':
        hisseler = BIST100_HISSE
        print(f"BIST100 endeksinden {len(hisseler)} hisse kontrol edilecek")
    elif hisse_giriş == 'BIST30':
        hisseler = BIST30 if BIST30 else BIST100_HISSE[:30]
        print(f"BIST30 endeksinden {len(hisseler)} hisse kontrol edilecek")
    elif hisse_giriş == 'BISTALL':
        from borsa_listesi import bist_sembollari_cek, tum_bist_hisselerini_getir
        hisseler = tum_bist_hisselerini_getir()
        print(f"TUM BIST hisselerinden {len(hisseler)} hisse kontrol edilecek")
    else:
        hisseler = [h.strip() for h in hisse_giriş.split(',')]
        print(f"{len(hisseler)} hisse kontrol edilecek: {hisseler}")

    # Verileri çek
    print(f"\n>> Veriler cekiliyor ({args.periyot})...")
    veriler = StockDataFetcher.veri_çek(hisseler, args.periyot)

    if not veriler:
        print("X Hic veri cekilemedi.")
        sys.exit(1)

    # Filtrele
    print(f"\n>> Filtreleme yapiliyor...")
    lister = StockLister(veriler)
    sonuçlar = lister.filtrele(args.indikatör, args.koşul)

    # Raporu yazdır
    lister.rapor_yazdır(sonuçlar, args.indikatör, args.koşul)

    # Dosyaya kaydet
    if args.çıktı and sonuçlar:
        with open(args.çıktı, 'w', encoding='utf-8') as f:
            f.write(f"Stock Lister Raporu\n")
            f.write(f"İndikatör: {args.indikatör}\n")
            f.write(f"Koşul: {args.koşul}\n")
            f.write(f"Tarih: {datetime.now()}\n\n")
            for hisse, bilgi in sonuçlar.items():
                f.write(f"{hisse}: {bilgi['değer']:.4f}\n")
        print(f"\n>> Sonuclar {args.çıktı} dosyasina kaydedildi.")


if __name__ == '__main__':
    main()
