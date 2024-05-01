from dataclasses import dataclass

import fake_user_agent

default_params = {
    "text": "Python Developer",
    "area": 0,  # All of Russia
    "enable_snippets": False,
    "items_on_page": 20,
    "page": 0,
    "search_period": 0,
    "experience": "doesNotMatter",
}
default_headers = {"User-Agent": fake_user_agent.user_agent()}


@dataclass
class SearchArea:
    Russia: int = 0
    Moscow: int = 1
    Saint_Petersburg: int = 2
    Yekaterinburg: int = 3
    Novosibirsk: int = 4
    AltayKrai: int = 1217
    Amur_obl: int = 1932
    Arkhangelsk_obl: int = 1008
    Belgorod_obl: int = 1817
    Bryansk_obl: int = 1828
    Vladimir_obl: int = 1716
    Volgograd_obl: int = 1511
    Vologda_obl: int = 1739
    Voronezh_obl: int = 1844
    DPR: int = 2134
    JAO: int = 1941
    Transbaikal_krai: int = 1192
    Zaporozhie: int = 2155
    Ivanovo_obl: int = 1754
    Irkutsk_obl: int = 1124
    KBR: int = 1464
    Kaliningrad_obl: int = 1020
    Kaluga_obl: int = 1859
    Kamchatka_krai: int = 1943
    KChR: int = 1471
    Kemerovo_obl: int = 1229
    Kirov_obl: int = 1661
    Kostroma_obl: int = 1771
    Krasnodar_krai: int = 1438
    Krasnoyarsk_krai: int = 1146
    Kurgan_obl: int = 1308
    Kursk_obl: int = 1880
    Leningrad_obl: int = 145
    Lipetsk_obl: int = 1890
    LPR: int = 2173
    Magadan_obl: int = 1946
    Moscow_obl: int = 2019
    Murmansk_obl: int = 1961
    NAD: int = 1985
    NizhnyNogvorod_obl: int = 1679
    Novgorod_obl: int = 1051
    Novosibirsk_obl: int = 1202
    Omsk_obl: int = 1249
    Orenburg_obl: int = 1563
    Oryol_obl: int = 1898
    Penza_obl: int = 1575
    Perm_obl: int = 1317
    Primorye_obl: int = 1948
    Pskov_obl: int = 1090
    Adyg_rep: int = 1422
    Altay_rep: int = 1216
    Baskortostan_rep: int = 1347
    Buryat_rep: int = 1118
    Dagestan_rep: int = 1424
    Ingush_rep: int = 1434
    Kalmyk_rep: int = 1553
    Karel_rep: int = 1077
    Komi_rep: int = 1041
    Crimea_rep: int = 2114
    MaryEl_rep: int = 1620
    Mordov_rep: int = 1556
    Sakha_rep: int = 1174
    Alania_rep: int = 1475
    Tatarstan_rep: int = 1624
    Tuva_rep: int = 1169
    Khakas_rep: int = 1187
    Rostov_obl: int = 1530
    Ryazan_obl: int = 1704
    Samara_obl: int = 1586
    Saratov_obl: int = 1596
    Sakhalin_obl: int = 1960
    Sverdlov_obl: int = 1261
    Smolensk_obl: int = 1103
    Stavropol_obl: int = 1481
    Tambov_obl: int = 1905
    Tver_obl: int = 1783
    Tomsk_obl: int = 1255
    Tula_obl: int = 1913
    Tyumen_obl: int = 1342
    Udmurt_rep: int = 1646
    Ulyanovsk_obl: int = 1614
    Khabarovsk_obl: int = 1975
    Yugra: int = 1368
    Kherson_obl: int = 2209
    Chelyabinsk_obl: int = 1984
    Chechen_rep: int = 1500
    Chuvash_rep: int = 1652
    Chukotka: int = 1982
    YNAD: int = 1414
    Yaroslavl_obl: int = 1806


class Currencies:
    Rub = "₽"
    Dollar = "$"
    Tenge = "₸"
    Euro = "€"


@dataclass
class Salary:
    min_salary: int | None
    max_salary: int | None
    currency: str | None
    brutto: bool | None


@dataclass
class Experience:
    min_exp: int | None
    max_exp: int | None


class EndOfCrawlError(Exception):
    pass


class UnknownError(Exception):
    pass


months_dict = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}
