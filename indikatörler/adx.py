"""
ADX (Average Directional Index) İndikatörü
Formül:
    +DM = High - High.shift(1) (pozitif yön hareketi)
    -DM = Low.shift(1) - Low (negatif yön hareketi)
    True Range = max(H-L, |H-PC|, |L-PC|)
    +DI = 100 * (+DM_smooted / TR)
    -DI = 100 * (-DM_smoothed / TR)
    DX = 100 * (|+DI - -DI| / (+DI + -DI))
    ADX = DX'in smoothing'i (tipik olarak 14 periyot EMA)
"""

import pandas as pd
import numpy as np


def hesapla(data: pd.DataFrame, periyot: int = 14) -> dict:
    """
    ADX indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: ADX periyodu (varsayılan: 14)

    Dönüş:
        dict: {'adx': ADX değeri, 'pozitif_di': +DI değeri, 'negatif_di': -DI değeri}
    """
    high = data['high']
    low = data['low']
    close = data['close']

    prev_close = close.shift(1)

    # True Range
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()

    # +DM ve -DM'yi sınırla (Wilder'ın yöntemi)
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    # Eşit zaman dilimlerinde sadece birini al
    both_positive = (plus_dm > 0) & (minus_dm > 0)
    both_negative = (plus_dm < 0) & (minus_dm < 0)

    plus_dm[both_negative] = 0
    minus_dm[both_positive] = 0

    # Smoothed TR, +DM, -DM (Wilder's smoothing)
    tr_smoothed = true_range.ewm(alpha=1/periyot, adjust=False).mean()
    plus_dm_smoothed = plus_dm.ewm(alpha=1/periyot, adjust=False).mean()
    minus_dm_smoothed = minus_dm.ewm(alpha=1/periyot, adjust=False).mean()

    # DI hesapla
    plus_di = 100 * (plus_dm_smoothed / tr_smoothed)
    minus_di = 100 * (minus_dm_smoothed / tr_smoothed)

    # DX hesapla
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

    # ADX = DX'in EMA'sı
    adx = dx.ewm(span=periyot, adjust=False).mean()

    return {
        'adx': adx,
        'pozitif_di': plus_di,
        'negatif_di': minus_di
    }


def sinyal_olustur(adx: pd.Series, pozitif_di: pd.Series, negatif_di: pd.Series,
                   adx_esigi: float = 25) -> pd.Series:
    """
    ADX sinyal üretir.

    Parametreler:
        adx: ADX değerleri
        pozitif_di: +DI değerleri
        negatif_di: -DI değerleri
        adx_esigi: ADX eşik değeri (varsayılan: 25)

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    sinyal = pd.Series(0, index=adx.index)

    # +DI, -DI'yı yukarı keserse = AL
    sinyal[(pozitif_di > negatif_di) & (pozitif_di.shift(1) <= negatif_di.shift(1))
           & (adx > adx_esigi)] = 1

    # -DI, +DI'yı yukarı keserse = SAT
    sinyal[(negatif_di > pozitif_di) & (negatif_di.shift(1) <= pozitif_di.shift(1))
           & (adx > adx_esigi)] = -1

    return sinyal
