# test_event_emitter.py

import pytest
import pytest_asyncio
import json
from unittest.mock import AsyncMock, patch
from .event_emitter import EventEmitter


@pytest_asyncio.fixture
async def event_emitter():
    with patch('aioipfs.AsyncIPFS') as mock_ipfs, patch('nats.aio.client.Client') as mock_nats:
        mock_ipfs_instance = mock_ipfs.return_value
        mock_nats_instance = mock_nats.return_value
        mock_ipfs_instance.add_json = AsyncMock(return_value="QmHash")
        mock_ipfs_instance.get_json = AsyncMock(return_value={"mocked": "data"})
        mock_nats_instance.jetstream = AsyncMock()
        mock_js = mock_nats_instance.jetstream.return_value

        emitter = EventEmitter()
        emitter.ipfs_client = mock_ipfs_instance
        emitter.nats_client = mock_nats_instance
        emitter.jetstream = mock_js

        return emitter


@pytest.mark.asyncio
async def test_emit_event(event_emitter):
    await event_emitter.emit_event("test_event", {"message": "Hello, world!"})
    event_emitter.ipfs_client.add_json.assert_called_once_with({"message": "Hello, world!"})
    event_emitter.jetstream.publish.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_event(event_emitter):
    mock_msg = AsyncMock()
    mock_msg.data = json.dumps({
        "data": {"message": "Hello, world!"},
        "previous_hash": "",
        "ipfs_hash": "QmHash",
        "compounded_hash": "test_hash"
    }).encode('utf-8')
    mock_msg.ack = AsyncMock()

    # Mock the pull subscription and its fetch method
    pull_subscription = AsyncMock()
    pull_subscription.fetch = AsyncMock(return_value=[mock_msg])
    event_emitter.jetstream.pull_subscribe = AsyncMock(return_value=pull_subscription)

    latest_event = await event_emitter.get_latest_event("test_event")
    assert latest_event["data"]["message"] == "Hello, world!"
    mock_msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_event_history(event_emitter):
    result = await event_emitter.retrieve_event_history("QmHash")
    assert result == {"mocked": "data"}
    event_emitter.ipfs_client.get_json.assert_called_once_with("QmHash")
