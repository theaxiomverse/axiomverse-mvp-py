import pytest
import logging
from src.modules.vectorchain import AxiomChain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_chain():
    chain = AxiomChain()
    try:
        # Initialize node
        identity = await chain.initialize_node("127.0.0.1")
        logger.info(f"Node initialized with: {identity}")

        # Start chain (this will create genesis)
        await chain.start()

        # Print state
        logger.info(f"Chain started successfully")
        logger.info(f"Node Identity: {chain.get_identity()}")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    finally:
        if chain:
            await chain.stop()