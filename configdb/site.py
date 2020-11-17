from enum import Enum, unique
import json
from typing import Dict, FrozenSet, Set, Union

from configdb.state import InstrumentState


@unique
class SiteCode(str, Enum):
    ALL = 'all'
    BPL = 'bpl'
    CIT = 'cit'
    COJ = 'coj'
    CPT = 'cpt'
    ELP = 'elp'
    LSC = 'lsc'
    MFG = 'mfg'
    NGQ = 'ngq'
    OGG = 'ogg'
    SOR = 'sor'
    SQA = 'sqa'
    TFN = 'tfn'
    TLV = 'tlv'
    TST = 'tst'
    WTF = 'wtf'


@unique
class TelescopeCode(Enum):
    TWO_METER_A = '2m0a'
    ONE_METER_A = '1m0a'
    FORTY_CENTIMETER_A = '0m4a'
    FORTY_CENTIMETER_B = '0m4b'
    FORTY_CENTIMETER_C = '0m4c'
    EIGHTY_CENTIMETER_A = '0m8a'


class Readout(object):
    def __init__(self, code: str, binning: int, name: str, overhead: float) -> None:
        self.code = code
        self.binning_x = binning
        self.binning_y = binning
        self.name = name
        self.overhead = overhead

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Readout):
            return NotImplemented

        return (self.code == o.code and
                self.name == o.name and
                self.binning_x == o.binning_x and
                self.binning_y == o.binning_y and
                self.overhead == o.overhead)

    def __hash__(self) -> int:
        return hash((self.code, self.name, self.binning_x, self.binning_y, self.overhead))

    def __str__(self) -> str:
        return f'{self.code}-{self.name}-binning_x-{self.binning_x}-binning_y-{self.binning_y}-overhead-{self.overhead}'


class Location(object):
    def __init__(self, latitude: float, longitude: float) -> None:
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Location):
            return NotImplemented

        return self.latitude == o.latitude and self.longitude == o.longitude

    def __hash__(self) -> int:
        return hash((self.latitude, self.longitude))


class InstrumentInfo(object):
    # TODO: Create a Readouts class to store the default Readout with the others
    def __init__(self, code: str, camera_codes: list, ag_code: str, instrument_type: str, default_readout: Union[Readout, None],
                 readouts: FrozenSet[Readout]) -> None:
        self.code = code
        self.camera_codes = camera_codes
        self.ag_code = ag_code
        self.instrument_type = instrument_type
        self.default_readout = default_readout
        self.readouts = readouts
        self.exposure_time = self._get_exposure_time()

    def __contains__(self, item):
        return (self._contains_readout_mode(item.readout_modes) and
                self._contains_ag_code(item.ag_code) and
                self._contains_code(item.code) and
                self._contains_instrument_type(item.instrument_type))

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, InstrumentInfo):
            return NotImplemented

        return (self.code == o.code and
                self.ag_code == o.ag_code and
                self.instrument_type == o.instrument_type and
                self.default_readout == o.default_readout and
                self.readouts == o.readouts and
                self.exposure_time == o.exposure_time)

    def __hash__(self):
        return hash((self.code, self.ag_code, self.instrument_type, self.default_readout, self.readouts,
                     self.exposure_time))

    def _contains_readout_mode(self, readout_modes: set) -> bool:
        for readout_mode in self.readouts:
            if readout_mode in readout_modes:
                return True

        return False

    # TODO: Do not return True for an empty string
    def _contains_code(self, code: str) -> bool:
        if code == self.code or code == '':
            return True

        return False

    def _contains_ag_code(self, ag_code: str) -> bool:
        if ag_code == self.ag_code or ag_code == '':
            return True

        return False

    # TODO: Do not return True for an empty string
    def _contains_instrument_type(self, instrument_type: str) -> bool:
        if instrument_type == self.instrument_type or instrument_type == '':
            return True

        return False

    def _get_exposure_time(self) -> int:
        sinistro_spectral_exposure_time_sec = 900
        default_exposure_time_sec = 300

        if self.instrument_type.upper() in ['1M0-SCICAM-SINISTRO', '2M0-SCICAM-SPECTRAL']:
            exposure_time = sinistro_spectral_exposure_time_sec
        else:
            exposure_time = default_exposure_time_sec

        return exposure_time


class Overheads(object):
    def __init__(self, per_exposure: float, front_padding: float, filter_change: float, config_change: float,
                 acquire_exposure: float):
        self.per_exposure = per_exposure
        self.front_padding = front_padding
        self.filter_change = filter_change
        self.config_change = config_change
        self.acquire_exposure = acquire_exposure

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Overheads):
            return NotImplemented

        return (self.per_exposure == o.per_exposure and
                self.front_padding == o.front_padding and
                self.filter_change == o.filter_change and
                self.config_change == o.config_change and
                self.acquire_exposure == o.acquire_exposure)

    def __hash__(self) -> int:
        return hash((self.per_exposure,
                     self.front_padding,
                     self.filter_change,
                     self.config_change,
                     self.acquire_exposure))


class Instrument(object):
    def __init__(self, info: InstrumentInfo, optical_elements: dict, site_code: SiteCode, observatory_code: str,
                 telescope_code: str, location: Location, overheads: Overheads, state: InstrumentState) -> None:
        self.info = info
        self.optical_elements = optical_elements
        self.site_code = site_code
        self.observatory_code = observatory_code
        self.telescope_code = telescope_code
        self.location = location
        self.overheads = overheads
        self.state = state
        self.telescope: Telescope

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Instrument):
            return NotImplemented

        return (self.info == o.info and
                self.optical_elements == o.optical_elements and
                self.site_code == o.site_code and
                self.observatory_code == o.observatory_code and
                self.telescope_code == o.telescope_code and
                self.location == o.location and
                self.overheads == o.overheads and
                self.state == o.state)

    def __hash__(self) -> int:
        return hash((self.info,
                     json.dumps(self.optical_elements, sort_keys=True),
                     self.site_code,
                     self.observatory_code,
                     self.telescope_code,
                     self.location,
                     self.overheads,
                     self.state))


class HaLimit(object):
    def __init__(self, positive: float, negative: float) -> None:
        self.positive = positive
        self.negative = negative


class Telescope(object):
    def __init__(self, code: str, horizon: float, ha_limit: HaLimit) -> None:
        self.code = code
        self.horizon = horizon
        self.ha_limit = ha_limit
        self.observatory: Observatory
        self.instruments: Set[Instrument] = set()

    def __str__(self) -> str:
        return self.code

    def add_instrument(self, instrument: Instrument) -> None:
        # TODO: Implement methods to make this work
        if instrument in self.instruments:
            raise ValueError(f'Instrument {instrument} already exists at telescope {self.code}')

        instrument.telescope = self
        self.instruments.add(instrument)


class Observatory(object):
    def __init__(self, code: str) -> None:
        self.code = code
        self.site: Site
        self.telescopes: Dict[str, Telescope] = {}

    def __str__(self) -> str:
        return self.code

    def add_telescope(self, telescope: Telescope) -> None:
        if telescope in self.telescopes:
            raise ValueError(f'Telescope {telescope} already exists at observatory {self.code}')

        telescope.observatory = self
        self.telescopes[telescope.code] = telescope


class Site(object):
    def __init__(self, code: SiteCode) -> None:
        self.code = code
        self.observatories: Dict[str, Observatory] = {}

    def __str__(self) -> str:
        return self.code.value

    def add_observatory(self, observatory: Observatory) -> None:
        if observatory.code in self.observatories.keys():
            raise ValueError(f'Observatory {observatory} already exists at site {self.code}')

        observatory.site = self
        self.observatories[observatory.code] = observatory


@unique
class Filter(Enum):
    air = 'air'
    B = 'B'
    C2 = 'C2'
    C3 = 'C3'
    clear = 'clear'
    CN = 'CN'
    CR = 'CR'
    D51 = 'D51'
    gp = 'gp'
    Ha = 'Ha'
    H_alpha = 'H-alpha'
    H_beta = 'H-beta'
    I = 'I'
    ip = 'ip'
    ND = 'ND'
    NH2 = 'NH2'
    OH = 'OH'
    OIII = 'OIII'
    Pinhole_150um = '150um-Pinhole'
    Pinhole_400um = '400um-Pinhole'
    R = 'R'
    rp = 'rp'
    Skymapper_VS = 'Skymapper-VS'
    solar = 'solar'
    U = 'U'
    up = 'up'
    UV = 'UV'
    V = 'V'
    w = 'w'
    Y = 'Y'
    zs = 'zs'
