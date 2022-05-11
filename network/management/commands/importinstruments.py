import logging
import requests

from django.conf import settings
from django.core.management.base import BaseCommand

#from calibrations.models import Filter, Instrument, InstrumentFilter
from network.models import Instrument
from configdb.configdb_connections import ConfigDBInterface

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generated Instrument and InstrumentFilter records from ConfigDB
    """

    configdb = ConfigDBInterface(settings.CONFIGDB_URL)

    def handle(self, *args, **options):
        logger.setLevel(options['verbosity'])

        logger.info(f'Getting instruments from {settings.CONFIGDB_URL}')
        # instruments_info = self.configdb.get_active_instruments_info()

        # for _, dome_instruments in instruments_info.items():
        #     for inst in dome_instruments:
        #
        #         i = Instrument.objects.get_or_create(code=inst['code'], site=inst['site'], telescope=inst['telescope'],
        #                                              enclosure=inst['observatory'])

        # for i in Instrument.objects.all():
        #     instrument_info = self.configdb.get_matching_instrument(site=i.site,
        #                                                             observatory=i.enclosure,
        #                                                             telescope=i.telescope)
        #     for optical_element in instrument_info.get('optical_elements', []):
        #         if optical_element.get('type') == 'filters':
        #             for oe in optical_element.get('optical_elements', []):
        
        #                 if Filter.objects.filter(name=oe['code']).exists():
        #
        #                     inst_filter = InstrumentFilter.objects.create(instrument=i,
        #                                                                   filter=Filter.objects.get(name=oe['code']))

        instruments_info = requests.get(f'{settings.CONFIGDB_URL}/instruments/').json()
        for inst in instruments_info.get('results', []):  # inst values come from the ConfigDB
            # TODO: filter SOAR
            if inst.get('instrument_type', {})['instrument_category'] == 'IMAGE' and inst.get('state') == 'SCHEDULABLE':  # get info for schedulable imagers
                # TODO: include COMMISSIONING
                site, enclosure, telescope, code = inst['__str__'].split('.')
                instrument = inst['__str__']
                instrument_type = inst['instrument_type']['code'].upper() # ConfigDB uses mixed-case. Calibration-TOM uses ALL CAPS.
                state = inst['state']
                if site == 'sor' or any(x in code for x in ['mc', 'xx']):  # TODO: include MuSCAT, exclude guide cameras
                    continue
                # instrument_fields values come from Calibration-TOM database
                #instrument_fields, _ = Instrument.objects.get_or_create(code=code, site=site, enclosure=enclosure, telescope=telescope)
                #instrument_fields, _ = Instrument.objects.get_or_create(code=code, instrument=instrument, instrument_type=instrument_type, state=state)
                instrument_fields, _ = Instrument.objects.get_or_create(code=code) # Use only the code to retrieve the Instrument from Calibration-TOM
                instrument_fields.instrument = instrument
                instrument_fields.instrument_type = instrument_type
                instrument_fields.state = state
                instrument_fields.save()
                #for camera in inst['science_cameras']:
                #    if camera['code'] == instrument_fields.code:
                #        instrument_fields.type = camera.get('camera_type', {}).get('code').upper()
                #        instrument_fields.save()
                #        oe_groups = camera.get('optical_element_groups', [])
                        #for oe_group in oe_groups:
                        #    if oe_group.get('type') == 'filters':
                        #        for oe in oe_group.get('optical_elements', []):
                        #            f = Filter.objects.filter(name=oe['code'])
                        #            if f.exists():
                        #                InstrumentFilter.objects.get_or_create(instrument=instrument_index, filter=f.first())
