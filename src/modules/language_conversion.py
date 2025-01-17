# language_conversion.py

def convert_lang_codes(lang_code):
    """
    Konwertuje dwuliterowy kod języka ISO 639-1 na trzyliterowy kod języka ISO 639-3.
   
    Argumenty:
    lang_code (str): Dwuliterowy kod języka ISO 639-1.
    Zwraca:
    str: Trzyliterowy kod języka ISO 639-3, jeśli istnieje w słowniku.
        Jeśli kod nie istnieje w słowniku, zwraca oryginalny kod.
    """    
    iso_639_conversion = {
        'aa': 'aar', 'ab': 'abk', 'af': 'afr', 'ak': 'aka', 'am': 'amh', 'ar': 'ara', 'as': 'asm',
        'av': 'ava', 'ay': 'aym', 'az': 'aze', 'ba': 'bak', 'be': 'bel', 'bg': 'bul', 'bh': 'bih',
        'bi': 'bis', 'bm': 'bam', 'bn': 'ben', 'bo': 'bod', 'br': 'bre', 'bs': 'bos', 'ca': 'cat',
        'ce': 'che', 'ch': 'cha', 'co': 'cos', 'cr': 'cre', 'cs': 'ces', 'cu': 'chu', 'cv': 'chv',
        'cy': 'cym', 'da': 'dan', 'de': 'ger', 'dv': 'div', 'dz': 'dzo', 'ee': 'ewe', 'el': 'ell',
        'en': 'eng', 'eo': 'epo', 'es': 'spa', 'et': 'est', 'eu': 'eus', 'fa': 'fas', 'ff': 'ful',
        'fi': 'fin', 'fj': 'fij', 'fo': 'fao', 'fr': 'fra', 'fy': 'fry', 'ga': 'gle', 'gd': 'gla',
        'gl': 'glg', 'gn': 'grn', 'gu': 'guj', 'gv': 'glv', 'ha': 'hau', 'he': 'heb', 'hi': 'hin',
        'ho': 'hmo', 'hr': 'hrv', 'ht': 'hat', 'hu': 'hun', 'hy': 'hye', 'hz': 'her', 'ia': 'ina',
        'id': 'ind', 'ie': 'ile', 'ig': 'ibo', 'ii': 'iii', 'ik': 'ipk', 'io': 'ido', 'is': 'isl',
        'it': 'ita', 'iu': 'iku', 'ja': 'jpn', 'jv': 'jav', 'ka': 'kat', 'kg': 'kon', 'ki': 'kik',
        'kj': 'kua', 'kk': 'kaz', 'kl': 'kal', 'km': 'khm', 'kn': 'kan', 'ko': 'kor', 'kr': 'kau',
        'ks': 'kas', 'ku': 'kur', 'kv': 'kom', 'kw': 'cor', 'ky': 'kir', 'la': 'lat', 'lb': 'ltz',
        'lg': 'lug', 'li': 'lim', 'ln': 'lin', 'lo': 'lao', 'lt': 'lit', 'lu': 'lub', 'lv': 'lav',
        'mg': 'mlg', 'mh': 'mah', 'mi': 'mri', 'mk': 'mkd', 'ml': 'mal', 'mn': 'mon', 'mo': 'mol',
        'mr': 'mar', 'ms': 'msa', 'mt': 'mlt', 'my': 'mya', 'na': 'nau', 'nb': 'nob', 'nd': 'nde',
        'ne': 'nep', 'ng': 'eng', 'nl': 'nld', 'nn': 'nno', 'no': 'nor', 'nr': 'nbl', 'nv': 'nav',
        'ny': 'nya', 'oc': 'oci', 'oj': 'oji', 'om': 'orm', 'or': 'ori', 'os': 'oss', 'pa': 'pan',
        'pi': 'pli', 'pl': 'pol', 'ps': 'pus', 'pt': 'por', 'qu': 'que', 'rm': 'roh', 'rn': 'run',
        'ro': 'ron', 'ru': 'rus', 'rw': 'kin', 'sa': 'san', 'sc': 'srd', 'sd': 'snd', 'se': 'sme',
        'sg': 'sag', 'si': 'sin', 'sk': 'slk', 'sl': 'slv', 'sm': 'smo', 'sn': 'sna', 'so': 'som',
        'sq': 'sqi', 'sr': 'srp', 'ss': 'ssw', 'st': 'sot', 'su': 'sun', 'sv': 'swe', 'sw': 'swa',
        'ta': 'tam', 'te': 'tel', 'tg': 'tgk', 'th': 'tha', 'ti': 'tir', 'tk': 'tuk', 'tl': 'tgl',
        'tn': 'tsn', 'to': 'ton', 'tr': 'tur', 'ts': 'tso', 'tt': 'tat', 'tw': 'twi', 'ty': 'tah',
        'ug': 'uig', 'uk': 'ukr', 'ur': 'urd', 'uz': 'uzb', 've': 'ven', 'vi': 'vie', 'vo': 'vol',
        'wa': 'wln', 'wo': 'wol', 'xh': 'xho', 'yi': 'yid', 'yo': 'yor', 'za': 'zha', 'zh': 'zho',
        'zu': 'zul'
    }
    return iso_639_conversion.get(lang_code, lang_code)