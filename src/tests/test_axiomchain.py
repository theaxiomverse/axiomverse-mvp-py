import pytest
import logging
from src.modules.vectorchain import AxiomChain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        identity = await chain.initialize_node("127.0.0.1")
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