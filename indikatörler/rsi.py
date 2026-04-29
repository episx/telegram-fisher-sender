"""
RSI (Relative Strength Index) İndikatörü
Formül: RSI = 100 - (100 / (1 + RS))
RS = Ortalama Kazanç / Ortalama Kayıp
"""

import pandas as pd
import numpy as np


def hesapla(data: pd.DataFrame, periyot: int = 14) -> pd.Series:
    """
    RSI indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: RSI hesaplama periyodu (varsayılan: 14)

    Dönüş:
        RSI değerleri (Series)
    """
    delta = data['close'].diff()

    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    avg_gain = gain.rolling(window=periyot).mean()
    avg_loss = loss.rolling(window=periyot).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def sinyal_olustur(rsi: pd.Series, astigi: float = 30, yukari: float = 70) -> pd.Series:
    """
    RSI sinyal üretir.

    Parametreler:
        rsi: RSI değerleri
        astigi: Aşırı satım seviyesi (varsayılan: 30)
        yukari: Aşırı alım seviyesi (varsayılan: 70)

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    sinyal = pd.Series(0, index=rsi.index)
    sinyal[rsi < astigi] = 1  # Al sinyali
    sinyal[rsi > yukari] = -1  # Sat sinyali
    return sinyal
