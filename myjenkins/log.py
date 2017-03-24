import logging


def setup_logging(verbose):
    """Configure logging."""
    if verbose >= 3:
        logger = logging.getLogger() # Root logger
    else:
        logger = logging.getLogger('myjenkins')

    if verbose >= 2:
        level = logging.DEBUG
    elif verbose >= 1:
        level = logging.INFO
    else:
        level = logging.ERROR

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
