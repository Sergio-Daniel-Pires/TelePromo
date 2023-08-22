from enum import Enum

class UserMessages(str, Enum):
    ALL_TAGS_MATCHED = (
        "**{}**: SUPER OFERTA PRA VOCE! 😱😱\n"   # Site name
        "\n"
        "🔥🔥🔥 {}\n"                             # Product name
        "\n"
        "💵 {:.2f}\n"                             # Price
        "\n"
        "🛒 {}\n"                                 # Link
    )

    AVG_LOW = (
        "**{}**: Baixou de preco!\n"      # Site name
        "\n"
        "🔥🔥 {}\n"                       # Product name
        "\n"
        "💵 {:.2f}\n"                     # Price
        "Hist.: {}\n"                     # AVG Price
        "\n"
        "🛒 {}\n"                         # Link
    )

    MATCHED_OFFER = (
        "**{}**: Você também pode gostar!\n"    # Site name
        "\n"
        "🔥 {}\n"                               # Product name
        "\n"
        "💵 {:.2f}"                             # Price
        "\n"
        "🛒 {}\n"                               # Link
    )
