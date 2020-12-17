import logging

from tom_observations.facility import get_service_class
from tom_observations.models import ObservationRecord
from tom_dataproducts.models import DataProduct, ReducedDatum
from tom_dataproducts.data_processor import run_data_processor

logger = logging.getLogger(__name__)


def observation_change_state(observation: ObservationRecord, previous_state):
    logger.info('Observation change state hook: %s from %s to %s', observation, previous_state, observation.status)

    # NRES RV calibration observation state change.
    # NOTE: this could be extracted into a method if desired

    if observation.status == 'COMPLETED':
        # the LCO facility knows about the data associated with this observation
        facility_class = get_service_class(observation.facility)()
        # ask the facility for the data
        data_products = facility_class.save_data_products(observation_record=observation)

        # run a data processor on each data product (creates ReducedDatums)
        for data_product in data_products:
            logger.info(f'processing {data_product}')
            # determine and set the data_product_type.
            data_product.data_product_type = 'nres_rv'
            # this specifies the processor according to settings.DATA_PRODUCT_TYPES
            reduced_datums = run_data_processor(data_product)

        # TODO 3 clean up the FITS file
        # remove FITS file b/c all data needed is in the ReducedDatum record
        # TODO 3a dissociate FITS file from data_product
        # TODO 3b remove FITS file

