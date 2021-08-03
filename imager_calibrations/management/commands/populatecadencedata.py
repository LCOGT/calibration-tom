from datetime import datetime, timedelta, timezone
import logging
from random import choice, randint

from django.core.management.base import BaseCommand
from tom_observations.models import DynamicCadence, ObservationRecord
from tom_targets.models import Target

from calibrations.models import InstrumentFilter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generated Instrument and InstrumentFilter records from ConfigDB
    """

    def handle(self, *args, **options):
        logger.setLevel(options['verbosity'])

        inst_filters = InstrumentFilter.objects.all()

        for inst_filter in inst_filters:
            dc = DynamicCadence.objects.get(cadence_parameters__instrument_code=inst_filter.instrument.code)
            og = dc.observation_group
            for i in range(0, randint(1, 5)):
                f = choice(InstrumentFilter.objects.filter(instrument=inst_filter.instrument))
                obsr = ObservationRecord.objects.create(
                    target=Target.objects.get(id=dc.cadence_parameters['target_id']),
                    facility='Imager Calibrations',
                    parameters={
                        f.filter.name: [True, f.filter.exposure_count, f.filter.exposure_time]
                    },
                    status=choice(['PENDING', 'COMPLETED', 'WINDOW_EXPIRED']),
                    scheduled_end=datetime(2021, 8, 3, 19, 10, 0, tzinfo=timezone.utc) - timedelta(days=(6 - i))
                )
                og.observation_records.add(obsr)
            og.save()
