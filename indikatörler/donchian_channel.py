"""
Donchian Channel İndikatörü
Formül:
    Upper Band = Highest High (N periyot)
    Middle Band = (Highest High + Lowest Low) / 2
    Lower Band = Lowest Low (N periyot)
"""

import pandas as pd


def hesapla(data: pd.DataFrame, periyot: int = 20) -> dict:
    """
    Donchian Channel indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: Kanal periyodu (varsayılan: 20)

    Dönüş:
        dict: {'yukari': Üst bant, 'orta': Orta bant, 'asagi': Alt bant}
    """
    high = data['high']
    low = data['low']

    highest_high = high.rolling(window=periyot).max()
    lowest_low = low.rolling(window=periyot).min()
    middle = (highest_high + lowest_low) / 2

    return {
        'yukari': highest_high,
        'orta': middle,
        'asagi': lowest_low
    }


def sinyal_olustur(data: pd.DataFrame, donchian: dict) -> pd.Series:
    """
    Donchian Channel sinyal üretir.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        donchian: Donchian Channel dict

    Dönüş:
        Sinyal serisi: 1 = al, -1 = sat, 0 = nötr
    """
    close = data['close']
    yukari = donchian['yukari']
    asagi = donchian['asagi']

    sinyal = pd.Series(0, index=close.index)

    # Fiyat üst banda çıkış = AL (breakout)
    sinyal[(close > yukari) & (close.shift(1) <= yukari.shift(1))] = 1

    # Fiyat alt banda iniş = SAT (breakout)
    sinyal[(close < asagi) & (close.shift(1) >= asagi.shift(1))] = -1

    return sinyal
