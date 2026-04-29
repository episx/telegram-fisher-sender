"""
Fisher Transform İndikatörü
Pine Script v6 ile tam uyumlu implementation:
    hl2 = (high + low) / 2
    high_ = ta.highest(hl2, len)
    low_ = ta.lowest(hl2, len)
    value = round_(.66 * ((hl2 - low_) / (high_ - low_) - .5) + .67 * nz(value[1]))
    fish1 = .5 * log((1 + value) / (1 - value)) + .5 * nz(fish1[1])
Aşırı alım: > 2, Aşırı satım: < -2
"""

import pandas as pd
import numpy as np


def hesapla(data: pd.DataFrame, periyot: int = 9) -> pd.Series:
    """
    Fisher Transform indikatörünü hesaplar (Pine Script v6 ile tam uyumlu).

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: Lookback periyodu (varsayılan: 9, Pine Script varsayılanı)

    Dönüş:
        Fisher Transform değerleri (Series)
    """
    # Pine Script: hl2 = (high + low) / 2 (Typical Price)
    hl2 = (data['high'] + data['low']) / 2

    # Pine Script: ta.highest(hl2, len) ve ta.lowest(hl2, len)
    # En yüksek ve en düşük hl2 değerleri
    highest_hl2 = hl2.rolling(window=periyot).max()
    lowest_hl2 = hl2.rolling(window=periyot).min()

    # Fiyat aralığı
    price_range = highest_hl2 - lowest_hl2
    price_range = price_range.replace(0, 1)  # Sıfıra bölmeyi önle

    # İteratif hesaplama için Series hazırla
    n = len(data)
    value = pd.Series(0.0, index=data.index)
    fish1 = pd.Series(0.0, index=data.index)

    for i in range(periyot, n):
        # Pine Script: val = round_(.66 * ((hl2 - low_) / (high_ - low_) - .5) + .67 * nz(value[1]))
        raw_val = 0.66 * ((hl2.iloc[i] - lowest_hl2.iloc[i]) / price_range.iloc[i] - 0.5)
        if i > periyot:
            raw_val += 0.67 * value.iloc[i - 1]

        # Pine Script: round_() clamps to [-0.999, 0.999]
        # val > .99 ? .999 : val < -.99 ? -.999 : val
        val = 0.999 if raw_val > 0.99 else (-0.999 if raw_val < -0.99 else raw_val)

        value.iloc[i] = val

        # Pine Script: fish1 := .5 * log((1 + value) / (1 - value)) + .5 * nz(fish1[1])
        fisher_val = 0.5 * np.log((1 + val) / (1 - val))
        if i > periyot:
            fisher_val += 0.5 * fish1.iloc[i - 1]

        fish1.iloc[i] = fisher_val

    return fish1


def sinyal_olustur(fisher: pd.Series, astigi: float = -2, yukari: float = 2) -> pd.Series:
    """
    Fisher Transform sinyal üretir.

    Parametreler:
        fisher: Fisher Transform değerleri
        astigi: Aşırı satım seviyesi (varsayılan: -2)
        yukari: Aşırı alım seviyesi (varsayılan: 2)

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    sinyal = pd.Series(0, index=fisher.index)

    # Fisher aşırı satım bölgesinden çıkış = AL
    sinyal[(fisher < astigi) & (fisher.shift(1) >= astigi)] = 1

    # Fisher aşırı alım bölgesinden çıkış = SAT
    sinyal[(fisher > yukari) & (fisher.shift(1) <= yukari)] = -1

    return sinyal
