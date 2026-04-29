"""
SMA (Simple Moving Average) İndikatörü
Formül: SMA = (N periyotun toplamı) / N
"""

import pandas as pd


def hesapla(data: pd.DataFrame, periyot: int = 20) -> pd.Series:
    """
    SMA indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: SMA periyodu (varsayılan: 20)

    Dönüş:
        SMA değerleri (Series)
    """
    sma = data['close'].rolling(window=periyot).mean()
    return sma


def sinyal_olustur(sma: pd.Series, fiyat: pd.Series) -> pd.Series:
    """
    SMA crossover sinyal üretir.

    Parametreler:
        sma: SMA değerleri
        fiyat: Kapanış fiyatı

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    sinyal = pd.Series(0, index=sma.index)
    sinyal[(fiyat > sma) & (fiyat.shift(1) <= sma.shift(1))] = 1
    sinyal[(fiyat < sma) & (fiyat.shift(1) >= sma.shift(1))] = -1
    return sinyal
