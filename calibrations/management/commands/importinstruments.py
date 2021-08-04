import logging
import requests

from django.conf import settings
from django.core.management.base import BaseCommand

from calibrations.models import Filter, Instrument, InstrumentFilter
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
        #         print(inst['code'])
        #         print(inst['site'])
        #         print(inst)
        #         i = Instrument.objects.get_or_create(code=inst['code'], site=inst['site'], telescope=inst['telescope'],
        #                                              enclosure=inst['observatory'])

        # for i in Instrument.objects.all():
        #     instrument_info = self.configdb.get_matching_instrument(site=i.site,
        #                                                             observatory=i.enclosure,
        #                                                             telescope=i.telescope)
        #     for optical_element in instrument_info.get('optical_elements', []):
        #         if optical_element.get('type') == 'filters':
        #             for oe in optical_element.get('optical_elements', []):
        #                 print(i.code)
        #                 print(oe['code'])
        #                 if Filter.objects.filter(name=oe['code']).exists():
        #                     print(oe['code'])
        #                     inst_filter = InstrumentFilter.objects.create(instrument=i,
        #                                                                   filter=Filter.objects.get(name=oe['code']))

        instruments_info = requests.get(f'{settings.CONFIGDB_URL}/instruments/').json()
        for inst in instruments_info.get('results', []):  # TODO: filter SOAR
            if inst.get('instrument_type', {})['instrument_category'] == 'IMAGE' and inst.get('state') == 'SCHEDULABLE':  # TODO: include COMMISSIONING
                site, enclosure, telescope, code = inst['__str__'].split('.')
                if site == 'sor' or any(x in code for x in ['mc', 'xx']):  # TODO: include MuSCAT, exclude guide cameras
                    continue
                i, _ = Instrument.objects.get_or_create(code=code, site=site, enclosure=enclosure, telescope=telescope)
                print(i.code)
                for camera in inst['science_cameras']:
                    if camera['code'] == i.code:
                        i.type = camera.get('camera_type', {}).get('code').upper()
                        i.save()
                        oe_groups = camera.get('optical_element_groups', [])
                        for oe_group in oe_groups:
                            if oe_group.get('type') == 'filters':
                                for oe in oe_group.get('optical_elements', []):
                                    f = Filter.objects.filter(name=oe['code'])
                                    if f.exists():
                                        InstrumentFilter.objects.get_or_create(instrument=i, filter=f.first())
