import logging

from django.core.management.base import BaseCommand
from tom_observations.models import DynamicCadence, ObservationGroup
from tom_targets.models import Target

from calibrations.models import Instrument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generated Instrument and InstrumentFilter records from ConfigDB
    """

    def handle(self, *args, **options):
        logger.setLevel(options['verbosity'])

        target = None
        for t in Target.objects.filter(targetextra__key='calibration_type', targetextra__value='IMAGER'):
            if t.target_is_in_season():
                target = t
                break
        else:
            raise Exception('No imager targets in season')

        for inst in Instrument.objects.all():
            og = ObservationGroup.objects.create(name=f'Photometric standard calibration for {inst.code}')
            DynamicCadence.objects.create(cadence_strategy='ImagerCadenceStrategy',
                                          cadence_parameters={
                                              'instrument_code': inst.code,
                                              'cadence_frequency': 24,
                                              'target_id': target.id
                                          },
                                          active=True,
                                          observation_group=og)
