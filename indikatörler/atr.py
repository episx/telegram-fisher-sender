"""
ATR (Average True Range) İndikatörü
Formül:
    True Range = max(H - L, |H - PC|, |L - PC|)
    ATR = True Range'ın 14 periyot SMA'sı
"""

import pandas as pd
import numpy as np


def hesapla(data: pd.DataFrame, periyot: int = 14) -> pd.Series:
    """
    ATR indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: ATR periyodu (varsayılan: 14)

    Dönüş:
        ATR değerleri (Series)
    """
    high = data['high']
    low = data['low']
    close = data['close']

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=periyot).mean()

    return atr


def pozisyon_büyüklüğü_hesapla(atr: pd.Series, sermaye: float, risk_percent: float = 2.0) -> pd.Series:
    """
    ATR bazlı pozisyon büyüklüğü hesaplar.

    Parametreler:
        atr: ATR değerleri
        sermaye: Toplam sermaye
        risk_percent: Risk yüzdesi (varsayılan: 2.0)

    Dönüş:
        Pozisyon büyüklüğü (Series)
    """
    risk_amount = sermaye * (risk_percent / 100)
    pozisyon = risk_amount / atr
    return pozisyon
