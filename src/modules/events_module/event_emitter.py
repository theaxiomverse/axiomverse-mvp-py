import asyncio
import json
import hashlib
from fastapi import HTTPException

from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
import aioipfs

from logging import getLogger
logger = getLogger(__name__)


def compute_hash(data: dict) -> str:
    event_json = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(event_json).hexdigest()


import asyncio
import json
import hashlib
from fastapi import HTTPException
import aiohttp
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext
import aioipfs
from logging import getLogger

logger = getLogger(__name__)


class EventEmitter:
    def __init__(self, nats_server="nats://localhost:4222"):
        self.nats_client = NATS()
        self.nats_server = nats_server
        self.jetstream: JetStreamContext = None
        self.ipfs_client = None
        self.http_session = None
        self._setup_done = False

    async def _setup(self):
        if not self._setup_done:
            self.http_session = aiohttp.ClientSession()
            self.ipfs_client = aioipfs.AsyncIPFS(session=self.http_session)
            await self.nats_client.connect(servers=[self.nats_server])
            self.jetstream = self.nats_client.jetstream()
            await self.create_stream()
            self._setup_done = True

    async def emit_event(self, event_type: str, data: dict) -> None:
        await self._setup()
        ipfs_hash = await self.ipfs_client.add_json(data)

        event = {
            "data": data,
            "ipfs_hash": ipfs_hash,
        }

        subject = f"events.{event_type}"
        message = json.dumps(event).encode('utf-8')
        await self.jetstream.publish(subject, message)

    async def cleanup(self):
        """Cleanup resources properly."""
        try:
            if self.nats_client and self.nats_client.is_connected:
                await self.nats_client.close()

            if self.ipfs_client:
                await self.ipfs_client.close()

            if self.http_session:
                await self.http_session.close()

            self._setup_done = False
            logger.info("EventEmitter cleanup completed")
        except Exception as e:
            logger.error(f"Error during EventEmitter cleanup: {e}")
            raise