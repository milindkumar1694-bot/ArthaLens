import pytest
from app.data.brokers.mock import MockBrokerProvider

@pytest.mark.asyncio
@pytest.mark.parametrize("symbol", ["NIFTY", "BANKNIFTY", "SENSEX", "INDIAVIX"])
async def test_mock_quotes_are_explicitly_labelled(symbol):
    quote = await MockBrokerProvider().get_quote(symbol)
    assert quote.symbol == symbol and quote.source == "mock" and quote.status == "ok"
