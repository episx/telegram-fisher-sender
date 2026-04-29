"""
Borsa Listesi - BIST hisse sembollerini çeker ve yönetir.
Bigpara API'den tüm BIST sembollerini çeker, local cache tutar.
"""

import requests
import json
import os
from pathlib import Path

# Cache dosyası
CACHE_DOSYASI = Path(__file__).parent / "bist_sembollar_cache.json"
CACHE_SURESI_GUN = 1  # Cache 1 gün geçerli
DELISTED_CACHE_DOSYASI = Path(__file__).parent / "delisted_stocks.json"

# Varsayılan BIST100 hisseleri (fallback - API çalışmazsa)
BIST100_HISSE = [
    'THYAO', 'EREGL', 'ASELS', 'GARAN', 'SAHOL', 'KCHOL', 'TUPRS',
    'ISCTR', 'YKBNK', 'AKBNK', 'HALKB', 'VAKBN',
    'KRDMD', 'CCOLA', 'SASA', 'PETKM', 'BIMAS',
    'FROTO', 'BRSAN', 'TOASO', 'HEKTS', 'SISE',
    'MGROS', 'TMSN', 'ODAS', 'ENKAI', 'KONYA', 'GUBRF',
    'ISBIR', 'SKTAS', 'KTLEV', 'DESPC', 'DERHL', 'KUTPO',
    'BRKSN', 'CMBT', 'CELHA', 'CEMAS', 'CLDMS', 'CMENT',
    'DOAS', 'ECILC', 'EGEEN', 'EGPRO', 'ERBOS', 'FLAP',
    'FONET', 'GOODY', 'GOZDE', 'GSDHO', 'HATEK', 'HEKTS',
    'IHLAS', 'INDES', 'ISMEN', 'KARTN', 'KCAER', 'KLGYO',
    'KLMSN', 'KLNMA', 'KNFRT', 'KONTR', 'KORDS', 'KRDMA',
    'KRDMB', 'MERIT', 'METRO', 'MIATK', 'MTRKS', 'NETAS',
    'NTGAZ', 'NTHOL', 'NUHCM', 'OBASE', 'ONCSM', 'OTKAR',
    'OYAKC', 'PARSN', 'PCILT', 'PENGY', 'PNSUT', 'PRKAB',
    'RALYH', 'SAFKR', 'SANKO', 'SEKFK', 'SILVR', 'SMART',
    'SOKE', 'SUNTK', 'TABGD', 'TAVHL', 'TCELL', 'TKFEN',
    'TKNSA', 'TMPOL', 'TRCAS', 'TSKB', 'TTKOM', 'TTRAK',
    'TUREX', 'ULAS', 'ULCAR', 'ULKER', 'UMPAS', 'UNYEC',
    'USDTR', 'VAKKO', 'VESBE', 'VESTL', 'VKING', 'YATAS',
    'YYAPI', 'YYLGD', 'ZOREN', 'ZTM'
]

# Varsayılan BIST30 hisseleri
BIST30 = BIST100_HISSE[:30]

# Varsayılan tüm hisseler (API'den çekilecek)
BIST_ALL_HISSE = []


def _cache_gecerli_mi() -> bool:
    """Cache dosyası geçerli mi kontrol eder"""
    if not CACHE_DOSYASI.exists():
        return False
    try:
        with open(CACHE_DOSYASI, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        cache_zamani = cache.get('tarih', '')
        if not cache_zamani:
            return False
        # Basit tarih kontrolü - sadece gün bazlı
        from datetime import datetime
        cache_tarih = datetime.fromisoformat(cache_zamani)
        su_an = datetime.now()
        fark = (su_an - cache_tarih).total_seconds() / 3600
        return fark < CACHE_SURESI_GUN * 24
    except:
        return False


def _cache_kaydet(sembollar: list):
    """Cache dosyasına kaydeder"""
    from datetime import datetime
    cache = {
        'tarih': datetime.now().isoformat(),
        'sembollar': sembollar
    }
    try:
        with open(CACHE_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception as e:
        print(f"Cache kaydetme hatası: {e}")


def bist_sembollari_cek() -> list:
    """
    Bigpara API'den tüm BIST sembollerini çeker.

    Dönüş:
        list: Sembol listesi (örn: ['THYAO', 'ASELS', ...])
    """
    global BIST_ALL_HISSE

    # Önce cache kontrol et
    if _cache_gecerli_mi():
        try:
            with open(CACHE_DOSYASI, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            BIST_ALL_HISSE = cache.get('sembollar', [])
            print(f"[Borsa] Cache'den {len(BIST_ALL_HISSE)} sembol yüklendi")
            return BIST_ALL_HISSE
        except:
            pass

    # API'den çek
    print("[Borsa] Bigpara API'den semboller çekiliyor...")
    sembollar = []

    try:
        url = "http://bigpara.hurriyet.com.tr/api/v1/hisse/list"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if 'data' in data:
                sembollar = [h['kod'] for h in data['data'] if h.get('kod')]
                print(f"[Borsa] Bigpara'dan {len(sembollar)} sembol alındı")
    except Exception as e:
        print(f"[Borsa] Bigpara API hatası: {e}")

    # Fallback: İnternet çalışmazsa local liste kullan
    if not sembollar:
        print("[Borsa] API çalışmadı, varsayılan liste kullanılıyor")
        # Local bilinen BIST hisselerinden oluşan geniş liste
        sembollar = [
            'THYAO', 'EREGL', 'ASELS', 'GARAN', 'SAHOL', 'KCHOL', 'TUPRS',
            'ISCTR', 'TCMB', 'YKBNK', 'AKBNK', 'HALKB', 'VAKBN', 'QNBFB',
            'KRDMD', 'CCOLA', 'SASA', 'PETKM', 'AYGAZ', 'BIMAS',
            'FROTO', 'BRSAN', 'TOASO', 'HEKTS', 'SISE', 'ENKAI',
            'Turkcell', 'MGROS', 'TMSN', 'ODAS', 'KONYA', 'GUBRF',
            'BAGC', 'IHLAS', 'ANEUS', 'ISBIR', 'SKTAS', 'KTLEV',
            'DESPC', 'DERHL', 'KUTPO', 'MAKIM', 'POLHO', 'SUMAS',
            'TIRE', 'BRKSN', 'CMBT', 'CELHA', 'CEMAS', 'CLDMS',
            'CMENT', 'COSMO', 'CRPOL', 'DGATE', 'DLEK', 'DNZ',
            'DOAS', 'DYOBY', 'ECILC', 'EDIP', 'EGEEN', 'EGPRO',
            'EKSEN', 'EMKEL', 'ENFES', 'ERBOS', 'ERD', 'FLAP',
            'FRIGO', 'FONET', 'GAREL', 'GENTS', 'GLYHO', 'GOODY',
            'GOZAS', 'GSDHO', 'HALKB', 'HATEK', 'HDFGS', 'HURGZ',
            'IDGYO', 'IHEVY', 'INDES', 'INTEM', 'ISMEN', 'ITFYO',
            'KAPLM', 'KARSN', 'KAYSE', 'KCAER', 'KERVT', 'KLGYO',
            'KLKIM', 'KLMSN', 'KLNMA', 'KNFRT', 'KONTR', 'KONYA',
            'KRONT', 'KRST', 'KRVGS', 'LIDFA', 'Link', 'LOGO',
            'LRSRO', 'MAKTK', 'MANAV', 'Mavik', 'MEDCO', 'MEGAP',
            'MEPET', 'MERIT', 'METRO', 'MGROS', 'MHRGY', 'MITRA',
            'MMCAS', 'MRDIN', 'NTHOL', 'NTGAZ', 'NUHCM', 'ONCSM',
            'ORCAY', 'OSMEN', 'OSTIM', 'OTKAR', 'OYAKC', 'PAMSG',
            'PARSN', 'PCOL', 'PENGY', 'PETKM', 'PNSUT', 'POLTK',
            'PRKAB', 'PRZMB', 'RALYH', 'REFIX', 'RUBNS', 'RYST',
            'SAFKR', 'SANKO', 'SEKFK', 'SEYKM', 'SGSOY', 'SILVR',
            'SMART', 'SOld', 'SOKE', 'SPOR', 'TACTR', 'TAKHE',
            'TANEL', 'TATKS', 'TBALF', 'TCELL', 'TEZOL', 'THYAO',
            'TKFEN', 'TKSHE', 'TLMAN', 'TNRSN', 'TOASO', 'TRILC',
            'TSKB', 'TSKPOR', 'TTKOM', 'TUCLK', 'TUKAS', 'TUPRS',
            'ULAS', 'ULCAR', 'UNLHC', 'UNYEC', 'USAK', 'UTPYO',
            'VERCF', 'VERUS', 'VESBE', 'VESTL', 'VKBLY', 'VOLT',
            'YAPRK', 'YATAS', 'YYILD', 'YYLND', 'ZORLD', 'ZTM',
            'AGHOL', 'AKSA', 'ALKIM', 'ARDYZ', 'BAGFS', 'BAYRK',
            'BLCON', 'BOYNR', 'BSOKE', 'CANM', 'CELIK', 'CEMEB',
            'COLK', 'CVKMD', 'DBGKY', 'DIRG', 'DYH', 'ECBYO',
            'EKSIO', 'EMNIS', 'ENKAI', 'ERAYD', 'ESCAR', 'GEDIK',
            'GENS', 'GOREV', 'GYOBOR', 'HOST', 'ISKIM', 'ISSEN',
            'JANTS', 'KAMN', 'KAPFA', 'KCAER', 'KSTUR', 'LCW',
            'MAHIBA', 'MERAS', 'MRM', 'MSGM', 'MSPH', 'MYPOL',
            'NIB', 'OLMDP', 'OMM', 'ORHEY', 'OSBAL', 'OYAYO',
            'PAGYO', 'PEKGY', 'PFDAN', 'PRKME', 'RNSAL', 'RTALB',
            'SADRA', 'SAHOC', 'SEBIR', 'SELGD', 'SERVE', 'SILK',
            'SNPAM', 'SOFEB', 'STLB', 'TCMD', 'TEPUB', 'TFFD',
            'TFLKT', 'TGS', 'TKN', 'TNAPI', 'TPEK', 'TPUB',
            'TRBYT', 'TRNSK', 'TTRAK', 'TUFGS', 'TUZD', 'TYD',
            'UFUK', 'ULAS', 'UNTAR', 'USIN', 'UVPYO', 'YONGA',
            'YYAPI', 'ZEGHD', 'KCHOL', 'SAHOL', 'VAKBN', 'GARAN',
            'AKBNK', 'ISCTR', 'YKBNK', 'QNBFB', 'SAFKK', 'KRDMD',
            'BRSAN', 'SISE', 'PETKM', 'Turkcell', 'CCOLA', 'FROTO',
            'HEKTS', 'SASA', 'ODAS', 'TMSN', 'KONYA', 'GUBRF',
            'KMPUR', 'CLNK', 'ODAS', 'BAGFS', 'KSTUR', 'LIDFA',
            'ISBIR', 'IHLAS', 'ANEUS', 'SKTAS', 'KTLEV', 'DESPC',
            'DERHL', 'KUTPO', 'MAKIM', 'POLHO', 'SUMAS', 'TIRE',
            'BRKSN', 'CMBT', 'CELHA', 'CEMAS', 'CLDMS', 'CMENT'
        ]

    if not sembollar:
        return BIST100_HISSE

    # Cache'e kaydet
    _cache_kaydet(sembollar)
    BIST_ALL_HISSE = sembollar

    return sembollar


def tum_bist_hisselerini_getir() -> list:
    """
    Tüm BIST hisselerini döndürür.
    Cache'den veya API'den çeker.
    """
    if BIST_ALL_HISSE:
        return BIST_ALL_HISSE
    return bist_sembollari_cek()


def bist100_hisselerini_getir() -> list:
    """BIST100 hisselerini döndürür"""
    all_stocks = tum_bist_hisselerini_getir()
    # İlk 100 veya hepsini döndür
    return all_stocks if len(all_stocks) <= 100 else all_stocks[:100]


def _delisted_oku() -> set:
    """Delisted cache dosyasından okur"""
    if not DELISTED_CACHE_DOSYASI.exists():
        return set()
    try:
        with open(DELISTED_CACHE_DOSYASI, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return set(data.get('sembollar', []))
    except:
        return set()


def delisted_stok_ekle(sembollar: list):
    """Verisi olmayan hisseleri delisted listesine ekler"""
    mevcut = _delisted_oku()
    yeni = set(sembollar) - mevcut
    if not yeni:
        return
    mevcut.update(yeni)
    try:
        with open(DELISTED_CACHE_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump({'sembollar': list(mevcut)}, f, ensure_ascii=False)
    except Exception as e:
        print(f"[Borsa] Delisted cache yazma hatasi: {e}")


def aktif_hisseleri_getir() -> list:
    """Delisted olmayan hisseleri döndürür"""
    all_stocks = tum_bist_hisselerini_getir()
    delisted = _delisted_oku()
    aktif = [s for s in all_stocks if s not in delisted]
    if delisted:
        print(f"[Borsa] {len(delisted)} delisted hisse atlandı: {list(delisted)[:10]}...")
    return aktif


# İlk çağırıldığında otomatik çek
if not BIST_ALL_HISSE:
    try:
        bist_sembollari_cek()
    except:
        pass
