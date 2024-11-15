import socket

import pytest
import logging
from src.modules.vectorchain import AxiomChain

# Configure logging to show info messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

logger = logging.getLogger(__name__)

def get_local_ip():
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external server (doesn't actually send any data)
        s.connect(('8.8.8.8', 80))
        # Get the local IP address
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return '127.0.0.1'


@pytest.fixture(autouse=True)
async def event_emitter_cleanup():
    yield
    # This will run after each test
    await cleanup_sessions()


async def cleanup_sessions():
    from src.modules.events_module.event_emitter import EventEmitter
    emitter = EventEmitter()
    await emitter.cleanup()


@pytest.mark.asyncio
async def test_chain():
    chain = AxiomChain()
    try:
        identity = await chain.initialize_node('216.209.218.112')
        logger.info(f"Node initialized with: {identity}")

        await chain.start()
        logger.info(f"Chain started successfully")
        logger.info(f"Node Identity: {chain.get_identity()}")

        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    finally:
        if chain:
            await chain.stop()