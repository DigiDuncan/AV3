import logging
import digiformatter.logger as digilogger

def setup_logging(name: str, level: int = logging.WARNING, show_source = False):
    dfhandler = digilogger.DigiFormatterHandler(show_source)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []
    logger.propagate = False
    logger.addHandler(dfhandler)
