### Logger ###
import logging

__all__ = ["logger"]

logger = logging.getLogger("LudusSMA")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
logger.addHandler(logging.StreamHandler())
logger.handlers[0].setFormatter(formatter)
