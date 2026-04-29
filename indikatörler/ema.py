"""
EMA (Exponential Moving Average) İndikatörü
Formül: EMA = (Close - EMA(önceki)) * Çarpan + EMA(önceki)
Çarpan = 2 / (Periyot + 1)
"""

import pandas as pd


def hesapla(data: pd.DataFrame, periyot: int = 20) -> pd.Series:
    """
    EMA indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: EMA periyodu (varsayılan: 20)

    Dönüş:
        EMA değerleri (Series)
    """
    ema = data['close'].ewm(span=periyot, adjust=False).mean()
    return ema


def sinyal_olustur(ema: pd.Series, fiyat: pd.Series) -> pd.Series:
    """
    EMA crossover sinyal üretir.

    Parametreler:
        ema: EMA değerleri
        fiyat: Kapanış fiyatı

    Dönüş:
        Sinyal serisi: 1 = al (fiyat EMA'yı yukarı keser), -1 = sat (fiyat EMA'yı aşağı keser), 0 = nötr
    """
    sinyal = pd.Series(0, index=ema.index)
    sinyal[(fiyat > ema) & (fiyat.shift(1) <= ema.shift(1))] = 1
    sinyal[(fiyat < ema) & (fiyat.shift(1) >= ema.shift(1))] = -1
    return sinyal
