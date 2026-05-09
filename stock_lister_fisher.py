"""
Stock Lister - Fisher Transform ile BIST Tarama
Otomatik olarak BIST'te Fisher Transform kosuluna uyan hisseleri listeler.
Kosul: fisher <= -1.5 veya fisher >= 1.5
Veri: Gundelik mumlar (1d)

Kullanim:
    python stock_lister_fisher.py
    python stock_lister_fisher.py --hisseler BIST100
    python stock_lister_fisher.py --hisseler BISTALL
    python stock_lister_fisher.py --hisseler THYAO,ASELS,GARAN
    python stock_lister_fisher.py --json-output data/oversold_today.json
"""

import sys
import argparse
from datetime import datetime
import os
import io
import json

from borsa_listesi import BIST100_HISSE, BIST30, tum_bist_hisselerini_getir
from indikatörler import fisher_hesapla


# === AYARLAR ===
INTERVAL = '1d'  # Gundelik mumlar
PERIYOT = '1mo'   # Veri periyodu (1mo, 3mo, 6mo, 1y)
FISHER_ALT_SINIR = -1.5
FISHER_UST_SINIR = 1.5
DEBUG = True      # Detayli debug ciktisi
# ===============


class StockDataFetcher:
    """Stock verisi cekici - toplu indirme"""

    @staticmethod
    def veri_çek(hisse_listesi: list, periyot: str = '1mo', interval: str = '1d', batch_size: int = 50) -> tuple:
        try:
            import yfinance as yf
        except ImportError:
            print("yfinance kurulu degil. pip install yfinance")
            sys.exit(1)

        veriler = {}
        hata_listesi = []

        # .IS suffix ekle
        yf_semboller = [f"{h}.IS" for h in hisse_listesi]

        print(f"[{len(yf_semboller)} hisse] Toplu indirme basliyor...")

        # yfinance uyarilarini sustur (stderr'yi yakala)
        stderr_backup = sys.stderr
        sys.stderr = io.StringIO()

        try:
            # Batch'ler halinde indir
            for i in range(0, len(yf_semboller), batch_size):
                batch = yf_semboller[i:i + batch_size]

                try:
                    data = yf.download(
                        batch,
                        period=periyot,
                        interval=interval,
                        group_by="ticker",
                        auto_adjust=True,
                        threads=True,
                        progress=False
                    )

                    if data.empty:
                        # Tüm batch boş
                        for hisse in batch:
                            hata_listesi.append((hisse.replace(".IS", ""), 'veri yok'))
                        continue

                    # Batch'teki hisselerin mevcut sembollerini al
                    try:
                        mevcut_semboller = data.columns.get_level_values(0).unique().tolist()
                    except Exception:
                        mevcut_semboller = []

                    # Her hisse için ayrı DataFrame'e çevir
                    for hisse in batch:
                        sembol = hisse.replace(".IS", "")
                        try:
                            hisse_df = data.xs(hisse, level=0, axis=1)

                            if hisse_df.empty:
                                hata_listesi.append((sembol, 'veri yok'))
                                continue

                            # Sütun isimlerini küçük harfe çevir
                            hisse_df.columns = [c.lower() for c in hisse_df.columns]
                            veriler[sembol] = hisse_df

                        except Exception as e:
                            hata_listesi.append((sembol, 'veri yok'))

                    # Batch'te istenen ama verisi gelmeyen hisseleri tespit et
                    for hisse in batch:
                        sembol = hisse.replace(".IS", "")
                        if sembol not in veriler and sembol not in [h[0] for h in hata_listesi]:
                            hata_listesi.append((sembol, 'veri yok'))

                except Exception as e:
                    # Batch tamamen hata verdiyse tümünü hatalı say
                    for hisse in batch:
                        hata_listesi.append((hisse.replace(".IS", ""), 'veri yok'))
        finally:
            sys.stderr = stderr_backup

        print(f"[OK] {len(veriler)}/{len(hisse_listesi)} hisse verisi alindi")

        return veriler, hata_listesi


def ana():
    parser = argparse.ArgumentParser(description='Fisher Transform BIST Tarama')
    parser.add_argument('--hisseler', type=str, default='BISTALL',
                        help='Hisse listesi: BIST100, BIST30, BISTALL veya virgulles ayrilmis semboller')
    parser.add_argument('--periyot', type=str, default=PERIYOT,
                        help=f'Veri periyodu (1mo, 3mo, 6mo, 1y). Varsayilan: {PERIYOT}')
    parser.add_argument('--json-output', type=str, default=None,
                        help='Oversold hisselerin yazilacagi JSON dosyasi yolu')

    args = parser.parse_args()

    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')

    # Hisse listesini belirle
    hisse_giris = args.hisseler.upper().strip()

    if hisse_giris == 'BIST100':
        hisseler = BIST100_HISSE
        print(f">>> BIST100 endeksinden {len(hisseler)} hisse taraniyor")
    elif hisse_giris == 'BIST30':
        hisseler = BIST30 if BIST30 else BIST100_HISSE[:30]
        print(f">>> BIST30 endeksinden {len(hisseler)} hisse taraniyor")
    elif hisse_giris == 'BISTALL':
        hisseler = tum_bist_hisselerini_getir()
        print(f">>> TUM BIST hisselerinden {len(hisseler)} hisse taraniyor")
    else:
        hisseler = [h.strip() for h in hisse_giris.split(',')]
        print(f">>> {len(hisseler)} hisse taraniyor: {hisseler}")

    print(f">>> Periyot: {args.periyot} | Interval: {INTERVAL}")

    print("\n" + "="*60)
    print("  FISHER TRANSFORM BIST TARAMASI")
    print("="*60)
    print(f"  Tarih: {tarih}")
    print(f"  Kosul: fisher <= {FISHER_ALT_SINIR} veya fisher >= {FISHER_UST_SINIR}")
    print("="*60)

    # Veri cek
    print("\n>>> Veriler cekiliyor...")
    veriler, hata_listesi = StockDataFetcher.veri_çek(hisseler, args.periyot, INTERVAL)

    if not veriler:
        print("\n! Hic veri cekilemedi.")
        return

    # Debug: Ilk hissenin veri yapisini kontrol et
    if DEBUG:
        ilk_hisse = list(veriler.keys())[0]
        ilk_data = veriler[ilk_hisse]
        print(f"\n[DEBUG] '{ilk_hisse}' veri yapsisi:")
        print(f"  Satir sayisi: {len(ilk_data)}")
        print(f"  Sutunlar: {list(ilk_data.columns)}")

    # Filtrele
    print("\n>>> Fisher Transform hesaplaniyor...\n")

    al_listesi = []
    sat_listesi = []
    hata_hisseler = []

    for hisse, data in veriler.items():
        try:
            fisher = fisher_hesapla(data)
            değer = fisher.iloc[-1]

            if değer <= FISHER_ALT_SINIR:
                al_listesi.append((hisse, değer))
            elif değer >= FISHER_UST_SINIR:
                sat_listesi.append((hisse, değer))

        except Exception as e:
            hata_hisseler.append(hisse)

    # Sonuclari sirala
    al_listesi.sort(key=lambda x: x[1])
    sat_listesi.sort(key=lambda x: x[1], reverse=True)

    # Rapor
    print("-"*60)

    if al_listesi:
        print(f"\n[OVERSOLD] ({len(al_listesi)} hisse)")
        print("-"*60)
        print(f"  {'Hisse':<10} {'Fisher':>10}")
        print("-"*60)
        for hisse, değer in al_listesi:
            print(f"  {hisse:<10} {değer:>10.4f}")
    else:
        print("\n[OVERSOLD] : yok")

    if sat_listesi:
        print(f"\n[OVERBOUGHT] ({len(sat_listesi)} hisse)")
        print("-"*60)
        print(f"  {'Hisse':<10} {'Fisher':>10}")
        print("-"*60)
        for hisse, değer in sat_listesi:
            print(f"  {hisse:<10} {değer:>10.4f}")
    else:
        print("\n[OVERBOUGHT] : yok")

    # Ozet
    toplam = len(al_listesi) + len(sat_listesi)
    başarılı = len(veriler) - len(hata_hisseler)
    print("\n" + "="*60)
    print(f"  OZET: {toplam} hisse tarama kosulunu karsiladi")
    print(f"        BASARILI TARAMALAR: {başarılı}/{len(veriler)}")
    print(f"        OVERSOLD: {len(al_listesi)} | OVERBOUGHT: {len(sat_listesi)}")

    if hata_hisseler:
        print(f"        ! {len(hata_hisseler)} hisse hesaplanamadi")
    if hata_listesi:
        print(f"        x {len(hata_listesi)} hisse veri hatasi (delisted olabilir)")
    print("="*60)

    # JSON cikti
    if args.json_output:
        oversold_data = {
            "scanned_at": datetime.now().isoformat(),
            "stocks": [
                {
                    "ticker": hisse,
                    "fisher": round(değer, 4),
                    "type": "oversold"
                }
                for hisse, değer in al_listesi
            ] + [
                {
                    "ticker": hisse,
                    "fisher": round(değer, 4),
                    "type": "overbought"
                }
                for hisse, değer in sat_listesi
            ]
        }
        os.makedirs(os.path.dirname(args.json_output), exist_ok=True)
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(oversold_data, f, indent=2, ensure_ascii=False)
        print(f"\n>>> JSON ciktisi kaydedildi: {args.json_output}")


if __name__ == '__main__':
    ana()