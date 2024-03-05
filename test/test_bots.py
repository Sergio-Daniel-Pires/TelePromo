from unittest.mock import MagicMock

import mongomock
import pytest
from fakeredis import FakeRedis

from project import utils
from project.bots import base
from project.monitor import Database, Monitoring, Vectorizers


@pytest.mark.parametrize(["bot_name", "category", "link"],
    [
        (
            "Adidas", "clothes",
            "https://www.adidas.com.br/api/plp/content-engine?query=flash_sale"
        ),
        (
            "Aliexpress", "eletronics",
            "https://pt.aliexpress.com/category/201000054/cellphones-telecommunications.html"
        ),
        (
            "Cobasi", "pets",
            "https://www.cobasi.com.br/promocoes"
        ),
        (
            "EstanteVirtual", "books",
            "https://www.adidas.com.br/api/plp/content-engine?query=flash_sale"
        ),
        (
            "Kabum", "eletronics",
            "https://www.adidas.com.br/api/plp/content-engine?query=flash_sale"
        ),
        (
            "Magalu", "eletronics",
            "https://www.magazineluiza.com.br/selecao/ofertasdodia/"
        ),
        (
            "Nike", "eletronics",
            "https://www.nike.com.br/_next/data/v10-331-0/nav/ofertas/emoferta.json"
        ),
        (
            "Pichau", "eletronics",
            "https://www.pichau.com.br"
        ),
        (
            "Shein", "clothes",
            "https://m.shein.com/br/new/WHATS-NEW-sc-00255950.html"
        ),
        (
            "Terabyte", "eletronics",
            "https://www.terabyteshop.com.br/promocoes"
        )
    ]
)
class TestSendWithoutApi:
    @pytest.mark.asyncio
    async def test_send (self, bot_name, category, link, redis_client: FakeRedis, request):
        # Prepare DB for requests
        db = Database(None, mongo_client=mongomock.MongoClient)

        vectorizers = Vectorizers()

        monitor = Monitoring(
            retry=3,
            database=db,
            vectorizer=vectorizers,
            redis_client=redis_client,
            metrics_collector=MagicMock()
        )

        ready_bots = [
            utils.brand_to_bot[bot_name](link=link, index=0, category=category)
        ]
        bot_results = await base.BotBase(ready_bots, True).run()

        for offer in bot_results:
            await monitor.send_offer_to_user(offer)