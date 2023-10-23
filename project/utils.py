import re

from project.bots import (
    Adidas, Aliexpress, Cobasi, EstanteVirtual, Kabum, MadeiraMadeira, Nike,
    Pichau, Shein, Terabyte
)

name_to_object = {
    "Adidas": Adidas.Adidas, "Aliexpress": Aliexpress.Aliexpress,
    "Cobasi": Cobasi.Cobasi, "EstanteVirtual": EstanteVirtual.EstanteVirtual,
    "Kabum": Kabum.Kabum, "MadeiraMadeira": MadeiraMadeira.MadeiraMadeira,
    "Nike": Nike.Nike, "Pichau": Pichau.Pichau, "Shein": Shein.Shein,
    "Terabyte": Terabyte.Terabyte
}

DAYS_IN_YEAR = 365
MINUTES_IN_DAY = 1440
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400

STOP_WORDS = (
    "", " ", "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "e", "com", "nao",
    "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi",
    "ao", "ele", "das", "tem", "a", "seu", "sua", "ou", "ser", "quando", "muito",
    "ha", "nos", "ja", "esta", "eu", "tambem", "so", "pelo", "pela", "ate", "isso",
    "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem",
    "nas", "me", "esse", "eles", "estao", "voce", "tinha", "foram", "essa", "num",
    "nem", "suas", "meu", "as", "minha", "tem", "numa", "pelos", "elas", "havia",
    "seja", "qual", "sera", "nos", "tenho", "lhe", "deles", "essas", "esses",
    "pelas", "este", "fosse", "dele", "tu", "te", "voces", "vos", "lhes", "meus",
    "minhas", "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos", "nossas",
    "dela", "delas", "esta", "estes", "estas", "aquele", "aquela", "aqueles",
    "aquelas", "isto", "aquilo", "estou", "esta", "estamos", "estao", "estive",
    "esteve", "estivemos", "estiveram", "estava", "estavamos", "estavam", "estivera",
    "estiveramos", "esteja", "estejamos", "estejam", "estivesse", "estivessemos",
    "estivessem", "estiver", "estivermos", "estiverem", "hei", "ha", "havemos",
    "hao", "houve", "houvemos", "houveram", "houvera", "houveramos", "haja", "hajamos",
    "hajam", "houvesse", "houvessemos", "houvessem", "houver", "houvermos", "houverem",
    "houverei", "houvera", "houveremos", "houverao", "houveria", "houveriamos",
    "houveriam", "sou", "somos", "sao", "era", "eramos", "eram", "fui", "foi", "fomos",
    "foram", "fora", "foramos", "seja", "sejamos", "sejam", "fosse", "fossemos",
    "fossem", "for", "formos", "forem", "serei", "sera", "seremos", "serao", "seria",
    "seriamos", "seriam", "tenho", "tem", "temos", "tem", "tinha", "tinhamos", "tinham",
    "tive", "teve", "tivemos", "tiveram", "tivera", "tiveramos", "tenha", "tenhamos",
    "tenham", "tivesse", "tivessemos", "tivessem", "tiver", "tivermos", "tiverem", "terei",
    "tera", "teremos", "terao", "teria", "teriamos", "teriam"
)


def normalize_str (text: str) -> str:
    text = text.lower()
    text = re.sub(r"[ãâáàä]", "a", text)
    text = re.sub(r"[êéèë]", "e", text)
    text = re.sub(r"[îíìï]", "i", text)
    text = re.sub(r"[õôóòö]", "o", text)
    text = re.sub(r"[ûúùü]", "u", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r",\s+|\.\s+|\s-\s", " ", text)

    return text
