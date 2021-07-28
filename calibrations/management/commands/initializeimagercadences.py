import logging

from django.core.management.base import BaseCommand
from tom_observations.models import DynamicCadence, ObservationGroup

from targeted_calibrations.models import Instrument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generated Instrument and InstrumentFilter records from ConfigDB
    """

    def handle(self, *args, **options):
        logger.setLevel(options['verbosity'])

        for inst in Instrument.objects.all():
            og = ObservationGroup.objects.create(name=f'Photometric standard calibration for {inst.code}')
            DynamicCadence.objects.create(cadence_strategy='ImagerCadenceStrategy',
                                          cadence_parameters={
                                              'instrument_code': inst.code,
                                              'cadence_frequency': 24,
                                              'target_id': 9  # TODO: this needs to be more dynamic
                                          },
                                          active=True,
                                          observation_group=og)
