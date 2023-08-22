import logging
from .models import Instrument

logger = logging.getLogger(__name__)

def instrument_post_save(instrument: Instrument, created: bool):
    logger.info(f'instrument_post_save hook: {instrument} created={created}')

