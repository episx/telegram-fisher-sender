"""
MACD (Moving Average Convergence Divergence) İndikatörü
Formül:
    MACD Line = 12 EMA - 26 EMA
    Signal Line = MACD'nin 9 periyot EMA'sı
    Histogram = MACD Line - Signal Line
"""

import pandas as pd


def hesapla(data: pd.DataFrame, hizli_per: int = 12, yavas_per: int = 26, sinyal_per: int = 9) -> dict:
    """
    MACD indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        hizli_per: Hızlı EMA periyodu (varsayılan: 12)
        yavas_per: Yavaş EMA periyodu (varsayılan: 26)
        sinyal_per: Sinyal çizgisi periyodu (varsayılan: 9)

    Dönüş:
        dict: {'macd': MACD çizgisi, 'sinyal': Sinyal çizgisi, 'histogram': Histogram}
    """
    ema_hizli = data['close'].ewm(span=hizli_per, adjust=False).mean()
    ema_yavas = data['close'].ewm(span=yavas_per, adjust=False).mean()

    macd = ema_hizli - ema_yavas
    sinyal = macd.ewm(span=sinyal_per, adjust=False).mean()
    histogram = macd - sinyal

    return {
        'macd': macd,
        'sinyal': sinyal,
        'histogram': histogram
    }


def sinyal_olustur(macd: pd.Series, sinyal: pd.Series, histogram: pd.Series) -> pd.Series:
    """
    MACD sinyal üretir.

    Parametreler:
        macd: MACD çizgisi
        sinyal: Sinyal çizgisi
        histogram: Histogram

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    sinyal_df = pd.Series(0, index=macd.index)

    # MACD, sinyal çizgisini yukarı keserse = AL
    sinyal_df[(macd > sinyal) & (macd.shift(1) <= sinyal.shift(1))] = 1

    # MACD, sinyal çizgisini aşağı keserse = SAT
    sinyal_df[(macd < sinyal) & (macd.shift(1) >= sinyal.shift(1))] = -1

    return sinyal_df
