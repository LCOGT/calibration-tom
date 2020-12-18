import logging
from astropy.io import fits
from astropy.time import Time

from tom_dataproducts.data_processor import DataProcessor
from tom_dataproducts.exceptions import InvalidFileFormatException
from tom_dataproducts.models import DataProduct

logger = logging.getLogger(__name__)


class NRESRVDataProcessor(DataProcessor):

    def process_data(self, data_product: DataProduct):
        # pull LCO-specific DATE_OBS from FITS file
        logger.info(f'Processing data product {data_product.data}')

        # TODO: find a way to extract the header efficiently
        data, header = fits.getdata(data_product.data.path, header=True)
        fits_date_obs = header.get('DATE_OBS')  # DATE_OBS is the documented header key for observation date
        date_obs_header_found = 'DATE_OBS'
        if not fits_date_obs:
            fits_date_obs = header.get('DATE-OBS')  # DATE-OBS is valid for older FITS files
            date_obs_header_found = 'DATE-OBS'
        try:
            logger.info(f'{date_obs_header_found} found in data_product with value {fits_date_obs}')
            data_timestamp = Time(fits_date_obs).to_datetime()
        except ValueError as e:
            logger.error(f'Unable to parse DATE_OBS from FITS file {data_product.data.path} into datetime: {e}')
            raise InvalidFileFormatException

        # pull the RV out of the FITS file
        radial_velocity = header.get('RADVEL')
        return [(data_timestamp, {'radial_velocity': radial_velocity})]
