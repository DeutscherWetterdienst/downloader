from .version import __version__
import logging
# default logger
logger = logging.getLogger("downloader")
logging.basicConfig(format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")