# Lemana Pro Region Mapping
# Maps regionId to city subdomain

LEMANA_REGION_SUBDOMAINS = {
    34: "moscow",  # Moscow and MO
    506: "spb",    # Saint Petersburg
    505: "krasnodar",
    508: "novosibirsk",
    509: "omsk",
    510: "voronezh",
    511: "ufa",
    715: "ekaterinburg",
    716: "volgograd",
    539: "krasnoyarsk",
    1437: "tver",
    1443: "tyumen",
    1447: "ryazan",
    1448: "kazan",
    2149: "chelyabinsk",
    2389: "novokuznetsk",
    2393: "kemerovo",
    2397: "barnaul",
    2949: "naberezhnye-chelny",
    3257: "penza",
    3258: "tula",
    3372: "yaroslavl",
    3399: "ulyanovsk",
    3402: "tolyatti",
    3428: "kostroma",
    3429: "kirov",
    3439: "saratov",
    3752: "stavropol",
    4124: "khabarovsk",
    4794: "orenburg",
    5057: "perm",
    5342: "irkutsk",
    5343: "petrozavodsk",
    6048: "kaliningrad",
    6062: "kursk",
    6063: "arkhangelsk",
    6395: "saransk",
    6466: "nizhniy-novgorod",
    6516: "cherepovets",
    6607: "kaluga",
    6609: "izhevsk",
    6725: "belgorod",
    7011: "vladikavkaz",
    7073: "novorossiysk",
    7138: "vladivostok",
    7278: "ivanovo",
    7290: "lipetsk",
    7874: "pskov",
    8157: "surgut",
    8232: "klin",
    8332: "smolensk",
    8492: "naro-fominsk",
}

def get_lemana_regional_url(base_url, region_id):
    """
    Adjusts the Lemana Pro URL based on the region_id.
    Simply replaces the subdomain (e.g., spb → klin) without adding query parameters.
    :param base_url: The original product URL
    :param region_id: The target region ID (int)
    :return: URL with replaced subdomain
    """
    if not base_url or 'lemanapro.ru' not in base_url:
        return base_url
    
    import re

    region_id = int(region_id)
    subdomain = LEMANA_REGION_SUBDOMAINS.get(region_id)
    
    # Remove any existing subdomain and replace with the new one
    # Pattern matches: spb.lemanapro.ru, moscow.lemanapro.ru, or just lemanapro.ru
    new_url = re.sub(r'^(https?://)([^.]+\.)?lemanapro\.ru', 
                     f'\\1{subdomain}.lemanapro.ru' if subdomain and region_id != 34 else '\\1lemanapro.ru',
                     base_url)
        
    return new_url
