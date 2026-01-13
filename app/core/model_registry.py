import asyncio
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    def __init__(self) -> None:
        self._loaded = False
        self.model = None

    async def load(self) -> None:
        logger.info("Loading model registry...")
        await asyncio.sleep(1)  # simulate I/O
        self.model = {"status": "loaded"}
        self._loaded = True
        logger.info("Model registry loaded")

    async def close(self) -> None:
        logger.info("Closing model registry...")
        self.model = None
        self._loaded = False
        logger.info("Model registry closed")
