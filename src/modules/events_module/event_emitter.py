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


class EventEmitter:
    def __init__(self, nats_server="nats://localhost:4222"):
        self.nats_client = NATS()
        self.nats_server = nats_server
        self.jetstream: JetStreamContext = None
        self.ipfs_client = aioipfs.AsyncIPFS()
        self.latest_hash = None

    async def connect(self):
        await self.nats_client.connect(servers=[self.nats_server])
        self.jetstream = self.nats_client.jetstream()
        await self.create_stream()

    async def create_stream(self):
        """
        Creates the 'events' stream in NATS JetStream if it does not exist.
        """
        try:
            await self.jetstream.add_stream(name="events", subjects=["events.*"], storage="file", max_msgs=100000,
                                            max_bytes=10 * 1024 * 1024 * 1024, retention="limits", discard="old")
            print("Stream 'events' created or already exists.")
        except Exception as e:
            print(f"Error creating stream: {e}")

    async def emit_event(self, event_type: str, data: dict) -> None:
        ipfs_hash = await self.ipfs_client.add_json(data)
        previous_hash = self.latest_hash if self.latest_hash else ""

        event = {
            "data": data,
            "previous_hash": previous_hash,
            "ipfs_hash": ipfs_hash,
        }

        event["compounded_hash"] = compute_hash(event)
        self.latest_hash = event["compounded_hash"]

        subject = f"events.{event_type}"
        message = json.dumps(event).encode('utf-8')
        await self.jetstream.publish(subject, message)

    async def get_latest_event(self, event_type: str) -> dict:
        subject = f"events.{event_type}"
        latest_event = None

        sub = await self.jetstream.pull_subscribe(subject, durable="my_durable_consumer")
        messages = await sub.fetch(1)

        if messages:
            msg = messages[0]
            latest_event = json.loads(msg.data.decode('utf-8'))
            await msg.ack()

        return latest_event

    async def retrieve_event_history(self, event_ipfs_hash: str) -> dict:
        """
        Retrieve an event from IPFS using the provided IPFS hash.
        """
        try:
            # Use `cat` to retrieve raw bytes from IPFS
            raw_data = await self.ipfs_client.cat(event_ipfs_hash)
            # Decode the bytes to string and parse it as JSON
            event_data = json.loads(raw_data.decode('utf-8'))
            return event_data
        except Exception as e:
            logger.error(f"Failed to retrieve event from IPFS: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve event from IPFS")
