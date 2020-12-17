import logging
from astropy.io import fits
from astropy.time import Time

from tom_dataproducts.data_processor import DataProcessor
from tom_dataproducts.models import DataProduct

logger = logging.getLogger(__name__)


class NRESRVDataProcessor(DataProcessor):

    def process_data(self, data_product: DataProduct):
        # pull LCO-specific DATE_OBS from FITS file
        fits_date_obs = fits.getval(data_product.data.path, 'DATE_OBS')
        data_timestamp = Time(fits_date_obs).to_datetime()

        # pull the RV out of the FITS file
        radial_velocity = fits.getval(data_product.data.path, 'RADVEL')
        return [(data_timestamp, radial_velocity)]



