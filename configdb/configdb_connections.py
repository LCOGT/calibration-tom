from http import HTTPStatus
import logging
import requests
from typing import List, Dict, Any, FrozenSet, Union

from deprecation import deprecated
from django.core.cache import cache

from configdb.site import SiteCode, Instrument, Readout, Location, Overheads, InstrumentInfo
from configdb.state import InstrumentState

logger = logging.getLogger(__name__)


class ConfigDBException(Exception):
    pass


class InstrumentNotFoundException(Exception):
    pass


class ConfigDBInterface(object):
    """
    Class for providing access to information in configdb. Used to replace both the camera_mappings file and
    the telescopes file. It saves/loads a local file of each from disk to use in case configdb is down.
    Proper usage is to call the update_configdb_structures once each scheduling run, then get the loaded
    in data as needed.
    """

    site_info: list

    def __init__(self, configdb_url):
        self.configdb_url = configdb_url
        if not self.configdb_url.endswith('/'):
            self.configdb_url += '/'
        self.get_site_info()

    @deprecated()
    def get_site_info(self, force_update=False):
        """
        Update stored site for the ConfigDBInterface instance by doing the following:
            - Get cached site info
            - If site info isn't cached, query ConfigDB for new data
            - If ConfigDBException, don't update site_info
        """
        cached_site_info = cache.get('configdb_site_info')

        if not cached_site_info or force_update:
            try:
                new_site_info = self._get_all_sites()
                cache.set('configdb_site_info', new_site_info)
                cached_site_info = new_site_info
                self.site_info = cached_site_info
            except ConfigDBException as e:
                logger.warning(f'update_site_info error with URL {self.configdb_url}: {e}. Reusing previous site info')
                return
        else:
            self.site_info = cached_site_info

    @deprecated()
    def _get_all_sites(self) -> dict:
        """
            Function returns the current structure of sites we can use for telescope info
        """
        try:
            sites_url = self.configdb_url + 'sites/'
            logger.debug(f"requests.get from {sites_url}")
            r = requests.get(sites_url)
        except requests.exceptions.RequestException as e:
            msg = "{}: {}".format(e.__class__.__name__, 'get_all_sites failed: ConfigDB connection down')

            raise ConfigDBException(msg)

        r.encoding = 'UTF-8'

        if not r.status_code == HTTPStatus.OK:
            raise ConfigDBException("get_all_sites failed: ConfigDB status code {}".format(r.status_code))

        json_results = r.json()

        if 'results' not in json_results:
            raise ConfigDBException("get_all_sites failed: ConfigDB returned no results")

        return json_results['results']

    @deprecated()
    def get_active_telescopes_info(self, site_code='all'):  # noqa
        """ Returns set of telescopes that are currently active """
        active_telescopes = {}
        for site in ConfigDBInterface.site_info:
            if (site['code'] == site_code or site_code == 'all') and site['active']:
                for enclosure in site['enclosure_set']:
                    if enclosure['active']:
                        for telescope in enclosure['telescope_set']:
                            if telescope['active']:
                                telcode = '{}.{}.{}'.format(site['code'], enclosure['code'], telescope['code'])
                                active_telescopes[telcode] = {
                                    'latitude': site['lat'],
                                    'longitude': site['long'],
                                    'restart': site['restart'],
                                    'timezone': site['tz'],
                                    'horizon': telescope['horizon'],
                                    'ha_limit_neg': telescope['ha_limit_neg'],
                                    'ha_limit_pos': telescope['ha_limit_pos']
                                }
        return active_telescopes

    @deprecated()
    def get_instruments_types(self, site_code: str = 'all') -> list:  # noqa
        """Returns a list of InstrumentType dictionaries
        """
        # TODO: define an site.InstrumentType class
        instrument_types: dict = {}  # use a dict to keep values unique; avoiding duplicates

        for site in ConfigDBInterface.site_info:
            if site['code'] == site_code or site_code == 'all':
                for enclosure in site['enclosure_set']:
                    for telescope in enclosure['telescope_set']:
                        for instrument in telescope['instrument_set']:
                            instrument_types[instrument['instrument_type']['code']] = {
                                'code': instrument['instrument_type']['code'],
                                'name': instrument['instrument_type']['name'],
                                }
        return list(instrument_types.values())  # just return the list of values

    @staticmethod
    def should_include_instrument(state: InstrumentState, everything: bool, commissioning: bool) -> bool:
        return everything or state == InstrumentState.SCHEDULABLE or (
                commissioning and state == InstrumentState.COMMISSIONING) or state == InstrumentState.STANDBY

    @deprecated()
    def get_active_instruments_info(self, site_code: str = 'all',
                                    instrument_type: str = '',
                                    include_commissioning: bool = True,
                                    include_everything: bool = False) -> dict:
        """ Returns set of instruments by telescope that are in schedulable or commissioning state """
        active_instruments = {}

        for site in self.site_info:
            if site['code'] == site_code or site_code == 'all':
                for enclosure in site['enclosure_set']:
                    for telescope in enclosure['telescope_set']:
                        for instrument in telescope['instrument_set']:
                            if not instrument_type or case_insensitive_equals(
                                    instrument['instrument_type']['code'], instrument_type):

                                state = InstrumentState[instrument['state'].upper()]

                                if self.should_include_instrument(state, include_everything, include_commissioning):
                                    telcode = '{}.{}.{}'.format(site['code'], enclosure['code'], telescope['code'])

                                    if telcode not in active_instruments:
                                        active_instruments[telcode] = []

                                    oegs = []
                                    oeg_change_time = 0
                                    for science_camera in instrument['science_cameras']:
                                        for oeg in science_camera['optical_element_groups']:
                                            oeg_change_time = max(oeg['element_change_overhead'], oeg_change_time)
                                            oegs.append(oeg)

                                    named_readout_modes = []
                                    default_readout_mode = None
                                    for mode_type in instrument['instrument_type']['mode_types']:
                                        if mode_type['type'] == 'readout':
                                            named_readout_modes = mode_type['modes']
                                            default_readout_mode = mode_type['default']
                                            break

                                    config_change_overheads = {
                                        config_type['code']: config_type['config_change_overhead'] for config_type in
                                        instrument['instrument_type']['configuration_types']}

                                    active_instruments[telcode].append({
                                        'state': instrument['state'].upper(),
                                        'site': site['code'],
                                        'observatory': enclosure['code'],
                                        'telescope': telescope['code'],
                                        'latitude': site['lat'],
                                        'longitude': site['long'],
                                        'horizon': telescope['horizon'],
                                        'ha_limit_neg': telescope['ha_limit_neg'],
                                        'ha_limit_pos': telescope['ha_limit_pos'],
                                        'instrument_type': instrument['instrument_type']['code'].upper(),
                                        'code': instrument['code'],
                                        'camera_codes': [sci_cam['code'] for sci_cam in instrument['science_cameras']],
                                        'ag_camera_type': instrument['autoguider_camera']['camera_type'][
                                            'code'].upper(),
                                        'ag_code': instrument['autoguider_camera']['code'],
                                        'optical_elements': oegs,
                                        'named_readout_modes': named_readout_modes,
                                        'default_readout_mode': default_readout_mode,
                                        'overheads': {
                                            'fixed_overhead_per_exposure': instrument['instrument_type'][
                                                'fixed_overhead_per_exposure'],
                                            'observation_front_padding': instrument['instrument_type'][
                                                'observation_front_padding'],
                                            'config_front_padding': instrument['instrument_type'][
                                                'config_front_padding'],
                                            'filter_change_time': oeg_change_time,
                                            'config_change_overhead': config_change_overheads,
                                            'acquire_exposure_time': instrument['instrument_type'][
                                                'acquire_exposure_time']
                                        }
                                    })
        return active_instruments

    @deprecated()
    def get_matching_instrument(self,
                                site='all',
                                observatory='',
                                telescope='',
                                instrument_type='',
                                instrument_name='',
                                include_everything=False):
        active_instruments = self.get_active_instruments_info(site_code=site, include_everything=include_everything)
        telcode = '{}.{}.{}'.format(site, observatory, telescope)

        for resource, active_insts in active_instruments.items():
            s, enc, tel = resource.split('.')
            if not observatory or observatory.lower() == enc.lower():
                if not telescope or telescope.lower() == tel.lower():
                    for instrument in active_insts:
                        if not instrument_type or instrument['instrument_type'].upper() == instrument_type.upper():
                            if not instrument_name or instrument['code'].lower() == instrument_name.lower():
                                return instrument

        raise InstrumentNotFoundException('Active instrument {} - {} not found on telescope {}. Either the instrument '
                                          'is not SCHEDULABLE or COMMISSIONING, or it does not exist.'
                                          .format(instrument_name, instrument_type, telcode))


def case_insensitive_equals(str1, str2):
    return str1.lower() == str2.lower()


def _is_spectrograph(instrument_type):
    return 'NRES' in instrument_type or 'FLOYDS' in instrument_type


@deprecated()
def _get_instruments(site_code: SiteCode, configdb_url: str) -> List[Instrument]:
    """
    Get a list of all instruments at a site
    """
    configdb = ConfigDBInterface(configdb_url)
    config_db_blob = configdb.get_active_instruments_info(site_code.value)

    instruments = []
    for instruments_at_site in config_db_blob.values():
        for instrument in instruments_at_site:
            if not _is_spectrograph(instrument['instrument_type']):
                instrument = _create_instrument(instrument)
                instruments.append(instrument)

    return instruments


@deprecated()
def _create_instrument(config_db_blob: Dict[str, Any]) -> Instrument:
    readouts = _get_readouts(config_db_blob['named_readout_modes'])
    default_readout = _get_default_readout(config_db_blob['default_readout_mode'], readouts)
    overheads = _get_overheads(config_db_blob['overheads'])

    info = InstrumentInfo(
        config_db_blob['code'],
        config_db_blob['camera_codes'],
        config_db_blob['ag_code'],
        config_db_blob['instrument_type'],
        default_readout,
        readouts
    )

    return Instrument(
        info,
        config_db_blob['optical_elements'],
        SiteCode(config_db_blob['site'].lower()),
        config_db_blob['observatory'],
        config_db_blob['telescope'],
        Location(config_db_blob['latitude'], config_db_blob['longitude']),
        overheads,
        InstrumentState(config_db_blob['state'])
    )


@deprecated()
def _get_default_readout(default_readout_str: str, readouts: FrozenSet[Readout]) -> Union[Readout, None]:
    for readout in readouts:
        if readout.code == default_readout_str:
            return readout

    return None


@deprecated()
def _get_readouts(readouts_dict: Dict[Any, Any]) -> FrozenSet[Readout]:
    readouts: List[Readout] = []

    for readout in readouts_dict:
        binning = readout['validation_schema'].get('extra_params', {}).get('bin_x', {}).get('default')
        readouts.append(Readout(readout['code'], binning, readout['name'], readout['overhead']))

    return frozenset(readouts)


@deprecated()
def _get_overheads(overheads_dict: Dict[Any, Any]) -> Overheads:
    return Overheads(
        overheads_dict['fixed_overhead_per_exposure'],
        overheads_dict['front_padding'],
        overheads_dict['filter_change_time'],
        overheads_dict['config_change_overheads'],
        overheads_dict['acquire_exposure_time'],
    )
