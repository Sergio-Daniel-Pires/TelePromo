import json
import time
from unittest.mock import MagicMock, patch

import mongomock
import pytest
from fakeredis import FakeRedis

from project.monitor import Database, Monitoring, Vectorizers


@pytest.mark.parametrize(["offer", "user_wishes"],
    [
        (
            'iphone_offer',
            [
                { "tags": [ "iphone" ], "user": "1", "max_price": 1000},
                { "tags": [ "iphone", "12mp" ], "user": "2", "max_price": 0 },
                { "tags": [ "iphone", "x", "verde", "256" ], "user": "3", "max_price": 0 },
                { "tags": [ "iphone" ], "user": "1", "max_price": 0, "blacklist": ["verde"]}
            ]
        ),
        (
            'bed_offer',
            [
                { "tags": [ "cama" ], "user": "1", "max_price": 1030 },
                { "tags": [ "cama", "casal" ], "user": "2", "max_price": 0 },
                { "tags": [ "cama", "casal", "cabeceira", "king" ], "user": "3", "max_price": 0 },
            ]
        )
    ]
)
class TestSendOk:
    @pytest.mark.asyncio
    async def test_send (self, offer, user_wishes, redis_client: FakeRedis, request):
        # Prepare DB for requests
        db = Database(None, mongo_client=mongomock.MongoClient)

        for user_wish in user_wishes:
            db.new_wish(**user_wish)

        vectorizers = Vectorizers()

        monitor = Monitoring(
            retry=3,
            database=db,
            vectorizer=vectorizers,
            redis_client=redis_client,
            metrics_collector=MagicMock()
        )
        monitor.tested_brands = { "Aliexpress", "Magalu" }

        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        for idx, pos in enumerate(( "third", "second", "first" )):
            last_sent = redis_client.lpop("msgs_to_send")
            assert last_sent, f"Don't send {pos}"
            assert json.loads(last_sent)["chat_id"] == str(3 - idx)

class TestDontSend:
    @pytest.mark.parametrize(["offer", "user_wishes"],
        [
            (
                'iphone_offer',
                [
                    { "tags": [ "iphone" ], "user": "1", "max_price": 900},
                ]
            ),
        ]
    )
    @pytest.mark.asyncio
    async def test_overpriced (self, offer, user_wishes, redis_client, request):
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
        monitor.tested_brands = { "Aliexpress", "Magalu" }

        for user_wish in user_wishes:
            monitor.database.new_wish(**user_wish)

        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        last_sent = redis_client.lpop("msgs_to_send")
        assert last_sent is None, "Overpriced has sent"

    @pytest.mark.parametrize(["offer", "user_wishes"],
        [
            (
                'iphone_offer',
                [
                    { "tags": [ "iphone" ], "user": "1", "max_price": 1000, "blacklist": ["preto"] },
                ]
            )
        ]
    )
    @pytest.mark.asyncio
    async def test_blacklisted (self, offer, user_wishes, redis_client: FakeRedis, request):
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
        monitor.tested_brands = { "Aliexpress", "Magalu" }

        for user_wish in user_wishes:
            monitor.database.new_wish(**user_wish)

        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        last_sent = redis_client.lpop("msgs_to_send")
        assert last_sent is None, "Blacklisted has sent"

    @pytest.mark.parametrize(["offer", "user_wishes"],
        [
            (
                'iphone_offer',
                [
                    { "tags": [ "iphone" ], "user": "1", "max_price": 1000 },
                ]
            )
        ]
    )
    @pytest.mark.asyncio
    async def test_repeated (self, offer, user_wishes, redis_client: FakeRedis, request):
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
        monitor.tested_brands = { "Aliexpress", "Magalu" }

        for user_wish in user_wishes:
            monitor.database.new_wish(**user_wish)

        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        first_send = redis_client.lpop("msgs_to_send")
        assert first_send is not None, "First need to send, because are not repeated"

        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        second_send = redis_client.lpop("msgs_to_send")
        assert second_send is None, "Second need to be blocked, because are repeated"

class TestSendAfter:
    @pytest.mark.parametrize(["offer", "user_wishes", "delay"],
        [
            (
                'iphone_offer',
                [
                    { "tags": [ "iphone" ], "user": "1", "max_price": 1000 }
                ],
                ((86400 * 3) + 100) # 3 days in seconds + 100 sec
            )
        ]
    )
    @patch('project.models.time')
    @pytest.mark.asyncio
    async def test_repeated_after_3_days (
        self, mock_time, offer, user_wishes, delay, redis_client: FakeRedis, request
    ):
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
        monitor.tested_brands = { "Aliexpress", "Magalu" }

        for user_wish in user_wishes:
            monitor.database.new_wish(**user_wish)

        mock_time.time = time.time
        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        first_send = redis_client.lpop("msgs_to_send")
        assert first_send is not None, "First need to send, because are not repeated"

        mock_time.time = lambda: time.time() + delay
        await monitor.send_offer_to_user(request.getfixturevalue(offer))

        second_send = redis_client.lpop("msgs_to_send")
        assert second_send is not None, "Second need to send, because three days have passed"
