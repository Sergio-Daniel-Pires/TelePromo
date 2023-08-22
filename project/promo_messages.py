from enum import Enum

class UserMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "*{}*: SUPER OFERTA PRA VOCE! 😱😱\n"   # Site name
        "\n"
        "🔥🔥🔥 {}\n"                           # Product name
        "\n"
        "R$ {:.2f} 💵"                          # Price
        "\n"
    )

    AVG_LOW = (
        "*{}*: Baixou de preco!\n"        # Site name
        "\n"
        "🔥🔥 {}\n"                       # Product name
        "\n"
        "R$ {:.2f} 💵\n"                  # Price
        "Hist.: {}\n"                     # AVG Price
        "\n"
    )

    MATCHED_OFFER = (
        "*{}*: Você também pode gostar!\n"    # Site name
        "\n"
        "🔥 {}\n"                             # Product name
        "\n"
        "R$ {:.2f} 💵"                        # Price
        "\n"
    )
