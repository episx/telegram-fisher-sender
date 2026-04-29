"""
Williams %R (Williams Percentage Range) İndikatörü
Formül: %R = -100 * (Highest High - Close) / (Highest High - Lowest Low)
Aşırı alım: > -20, Aşırı satım: < -80
"""

import pandas as pd


def hesapla(data: pd.DataFrame, periyot: int = 14) -> pd.Series:
    """
    Williams %R indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: Hesaplama periyodu (varsayılan: 14)

    Dönüş:
        Williams %R değerleri (Series, -100 ile 0 arasında)
    """
    high = data['high']
    low = data['low']
    close = data['close']

    highest_high = high.rolling(window=periyot).max()
    lowest_low = low.rolling(window=periyot).min()

    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))

    return williams_r


def sinyal_olustur(williams_r: pd.Series, astigi: float = -80, yukari: float = -20) -> pd.Series:
    """
    Williams %R sinyal üretir.

    Parametreler:
        williams_r: Williams %R değerleri
        astigi: Aşırı satım seviyesi (varsayılan: -80)
        yukari: Aşırı alım seviyesi (varsayılan: -20)

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    sinyal = pd.Series(0, index=williams_r.index)

    # Williams %R aşırı satım bölgesinden çıkış = AL
    sinyal[(williams_r < astigi) & (williams_r.shift(1) >= astigi)] = 1

    # Williams %R aşırı alım bölgesinden çıkış = SAT
    sinyal[(williams_r > yukari) & (williams_r.shift(1) <= yukari)] = -1

    return sinyal
