"""
Bollinger Bands İndikatörü
Formül:
    Orta Bant = 20 periyot SMA
    Üst Bant = Orta Bant + (2 * Standart Sapma)
    Alt Bant = Orta Bant - (2 * Standart Sapma)
"""

import pandas as pd


def hesapla(data: pd.DataFrame, periyot: int = 20, std_mult: float = 2.0) -> dict:
    """
    Bollinger Bands indikatörünü hesaplar.

    Parametreler:
        data: OHLCV verisi (DataFrame)
        periyot: Periyot (varsayılan: 20)
        std_mult: Standart sapma çarpanı (varsayılan: 2.0)

    Dönüş:
        dict: {'orta': Orta bant, 'ust': Üst bant, 'alt': Alt bant}
    """
    orta = data['close'].rolling(window=periyot).mean()
    std = data['close'].rolling(window=periyot).std()

    ust = orta + (std_mult * std)
    alt = orta - (std_mult * std)

    return {
        'orta': orta,
        'ust': ust,
        'alt': alt
    }


def sinyal_olustur(bollinger: dict, fiyat: pd.Series) -> pd.Series:
    """
    Bollinger Bands sinyal üretir.

    Parametreler:
        bollinger: Bollinger Bands değerleri
        fiyat: Kapanış fiyatı

    Dönüş:
        Sinyal serisi: 1 = al (fiyat alt banda temas), -1 = sat (fiyat üst banda temas), 0 = nötr
    """
    alt = bollinger['alt']
    ust = bollinger['ust']
    sinyal = pd.Series(0, index=fiyat.index)

    # Fiyat alt banda temas ettiğinde al
    sinyal[(fiyat < alt) & (fiyat.shift(1) >= alt.shift(1))] = 1

    # Fiyat üst banda temas ettiğinde sat
    sinyal[(fiyat > ust) & (fiyat.shift(1) <= ust.shift(1))] = -1

    return sinyal
